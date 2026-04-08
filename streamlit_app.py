import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import difflib
import re

# -------------------------------
# 1. THE IMMORTAL VISION ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

def get_herb_aliases(herb_name):
    """Maps actual herb names to known OCR hallucinations."""
    aliases = []
    mapping = {
        "healing sunflower": ["healing", "sunflower", "sundlng", "hcalig", "healig", "sunllower", "sunllowe", "hcaling", "suadlag", "hlcaling", "hedig", "heali4g", "heallig", "bzealig", "sqnllowcc", "sannhg", "ealv"],
        "black iron root": ["black", "ironroot", "ionadoot", "bladz", "bonroor", "bouroot", "bladk", "kourooc", "bledk", "koro", "koroo", "bled", "korooz", "@ladk", "jaurooz", "iecat", "ko", "rooz"],
        "blue wave coral herb": ["blue", "wave", "coral", "ballaz", "coaileb", "ualheb", "oalhub", "blugwav", "blugwavg", "uallub", "qbal", "ualleb", "dallazz", "blwu", "wlaw", "cucallld", "sazglxb"],
        "thousand year lotus": ["thousand", "lotus", "hatsud", "yealoug", "yeaclos", "ibousand", "tbousand", "uouard", "iboutnd", "ycclas", "yatoud", "yac", "obuesacd", "yatoud"],
        "moonlight jade leaf": ["moonlight", "jadeleaf", "saglui", "mopnlight", "meccligbt", "jadalzar", "jadeleal", "jadelea", "mooclight", "meonligbt", "jadglca", "saal", "meuuligbt", "saglti", "eeeclgb", "adulal", "jaclu", "8na3z", "saglti"],
        "ironbone grass": ["ironbone", "gtass", "iobge", "kuboue", "ouboue", "bonbone", "konbong", "iabssa", "gcass", "iabge", "leuboue", "laza", "otz"],
        "nine suns flame grass": ["ninesuns", "flamegrass"],
        "purple lightning orchid": ["purple", "orchid", "lightning", "bistadattg", "ruplg", "lipnnidg", "eunte"],
        "red ginseng": ["ginseng", "red"],
        "bitter jade grass": ["bitter", "jadegrass"],
        "cloud mist herb": ["cloud", "mist", "mistherb", "candmse", "hedb", "dudsb", "hub"],
        "spirit spring herb": ["spiritspring", "springherb"],
        "dandelion of qi": ["dandelion", "ofqi"],
        "seven star flower": ["sevenstar", "starflower", "setcnsaac", "flower", "sevez", "sur", "8lst", "fte"],
        "starlight dew herb": ["starlight", "dewherb"],
        "heavenly spirit vine": ["heavenly", "spiritvine"],
        "mountain green herb": ["mountain", "greenherb"],
        "wild spirit grass": ["wildspirit", "wild", "budspide", "gas3", "wnika", "spinft", "eapnn"],
        "azure serpent grass": ["azure", "serpent"],
        "wild bitter grass": ["wildbitter", "bittergrass"],
        "silverleaf herb": ["silverleaf", "silver"],
        "crimson flame mushroom": ["crimson", "flame", "mushroom"]
    }
    if herb_name.lower() in mapping:
        aliases.extend(mapping[herb_name.lower()])
    return list(set(aliases))

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # ⚡ Speed Scaling
    h, w = img_cv.shape[:2]
    scale = 1000 / w
    img_cv = cv2.resize(img_cv, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 🧪 Contrast Stretching
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    xp = [0, 64, 128, 192, 255]
    fp = [0, 16, 128, 240, 255]
    x = np.arange(256)
    table = np.interp(x, xp, fp).astype('uint8')
    processed = cv2.LUT(gray, table)
    
    results = reader.readtext(processed, text_threshold=0.3)
    
    curr_h, curr_w = processed.shape[:2]
    numbers_found = []
    herbs_found = []
    raw_text_seen = []
    
    for bbox, text, prob in results:
        raw_text_seen.append(text)
        clean = text.lower().replace(' ', '')
        
        # Quantity Cleanup
        clean = clean.replace('xz', 'x12').replace('xlz', 'x12').replace('xiz', 'x12').replace('x22', 'x12').replace('x[223', 'x12')
        if clean == '22': clean = 'x2'
        
        clean = clean.replace('i', '1').replace('|', '1').replace('l', '1').replace('s', '5').replace('o', '0').replace('z', '2')
        
        cx = (bbox[0][0] + bbox[1][0]) / 2
        cy = (bbox[0][1] + bbox[2][1]) / 2
        
        if ('x' in clean or any(c.isdigit() for c in clean)) and len(clean) < 7:
            nums = ''.join(filter(str.isdigit, clean))
            if nums:
                numbers_found.append({'qty': int(nums), 'x': cx, 'y': cy})
        else:
            word = re.sub(r'[^a-z0-9]', '', text.lower())
            if len(word) >= 3:
                matched_herb = None
                for herb in herb_list:
                    aliases = get_herb_aliases(herb)
                    if any(alias in word for alias in aliases):
                        matched_herb = herb
                        break
                    for alias in aliases:
                        if len(alias) > 3 and difflib.SequenceMatcher(None, word, alias).ratio() > 0.65:
                            matched_herb = herb
                            break
                    if matched_herb: break
                if matched_herb:
                    herbs_found.append({'herb': matched_herb, 'x': cx, 'y': cy})

    found_data = {}
    for h_frag in herbs_found:
        best_num = None
        min_dist = float('inf')
        for num in numbers_found:
            y_diff = h_frag['y'] - num['y']
            x_diff = abs(h_frag['x'] - num['x'])
            if 0 < y_diff < (curr_h * 0.25) and x_diff < (curr_w * 0.15):
                dist = (x_diff**2 + y_diff**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    best_num = num
        if best_num:
            herb = h_frag['herb']
            if herb not in found_data or best_num['qty'] > found_data[herb]:
                found_data[herb] = best_num['qty']
                
    return found_data, raw_text_seen

# -------------------------------
# 2. FULL RECIPE DATABASE (Restored)
# -------------------------------
def get_db():
    return {
        "Nine Yang Pill": [
            {"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92},
            {"tier": "Heavenly", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "black iron root": 2, "crimson flame mushroom": 1}, "qi": 120}
        ],
        "Jade Tide Pill": [
            {"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150},
            {"tier": "Heavenly", "ingredients": {"blue wave coral herb": 2, "black iron root": 1, "crimson flame mushroom": 1, "bitter jade grass": 2}, "qi": 162}
        ],
        "Stormheart Pill": [{"tier": "Heavenly", "ingredients": {"cloud mist herb": 4, "spirit spring herb": 2}, "qi": 225}],
        "Lotus Nirvana Pill": [{"tier": "Standard", "ingredients": {"thousand year lotus": 6}, "qi": 50}],
        "Starborn Agility Pill": [
            {"tier": "Imperfect", "ingredients": {"dandelion of qi": 1, "seven star flower": 2, "blue wave coral herb": 1, "cloud mist herb": 1, "spirit spring herb": 1}, "qi": 115},
            {"tier": "Heavenly", "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230}
        ],
        "Seven Star Enlightenment": [
            {"tier": "Heavenly (Lotus)", "ingredients": {"thousand year lotus": 2, "blue wave coral herb": 1, "heavenly spirit vine": 1, "starlight dew herb": 2}, "qi": 285},
            {"tier": "Heavenly (Pure)", "ingredients": {"heavenly spirit vine": 1, "starlight dew herb": 5}, "qi": 295}
        ],
        "Dragon Essence Pill": [
            {"tier": "Standard", "ingredients": {"azure serpent grass": 1, "purple lightning orchid": 1, "nine suns flame grass": 1, "crimson flame mushroom": 2, "cloud mist herb": 1}, "qi": 0, "spec": "18% Lifespan"},
            {"tier": "Heavenly", "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"}
        ],
        "Sun Roses Rebirth": [{"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"}],
        "Soul Replenishing": [{"tier": "Heavenly", "ingredients": {"healing sunflower": 2, "red ginseng": 1, "ironbone grass": 2, "seven star flower": 1}, "qi": 0, "spec": "12% Lifespan (Perm)"}]
    }

# -------------------------------
# 3. APP UI
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")
st.markdown("<style>.stApp { background: #0a0c10; color: white; }</style>", unsafe_allow_html=True)

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

for h in all_herbs:
    if f"i_{h}" not in st.session_state: st.session_state[f"i_{h}"] = 0
if 'debug_log' not in st.session_state: st.session_state['debug_log'] = []

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

with tab2:
    ss_file = st.file_uploader("Upload Inventory Screenshot", type=['png', 'jpg', 'jpeg'])
    if ss_file:
        if st.button("✨ Decompile Image"):
            with st.spinner("Decoding Herbs..."):
                found, raw_text = decompile_screenshot(ss_file, all_herbs)
                st.session_state['debug_log'] = raw_text
                if found:
                    for herb, qty in found.items(): st.session_state[f"i_{herb}"] += qty
                    st.success(f"Added {len(found)} herbs!")
                    st.rerun()

    if st.session_state['debug_log']:
        with st.expander("🛠️ View Raw AI Data"): st.write(st.session_state['debug_log'])
    
    st.divider()
    h_search = st.text_input("🔍 Search Inventory...", "").lower()
    cols = st.columns(2)
    filtered = [h for h in all_herbs if h_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 2]: st.number_input(h.title(), min_value=0, key=f"i_{h}")

with tab1:
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    craftable = []
    for name, variants in db.items():
        for v in variants:
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            if amt > 0: craftable.append({"name": name, "tier": v["tier"], "amt": amt, "qi": v["qi"], "spec": v.get("spec"), "ing": v["ingredients"]})

    if craftable:
        for p in craftable:
            st.write(f"### {p['name']} ({p['tier']}) - Batch: {p['amt']}")
            st.write(f"Ingredients: {p['ing']}")
    else:
        st.info("No craftable items. Add herbs to your chest!")
