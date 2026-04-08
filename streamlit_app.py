import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import difflib
import re

# -------------------------------
# 1. ENHANCED OCR & VISION ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    """Loads OCR engine into memory."""
    return easyocr.Reader(['en'], gpu=False)

def preprocess_image(img_np):
    """Enhance image for OCR (Grayscale -> Thresholding)"""
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    # Makes text pop against game backgrounds
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return gray

def get_herb_aliases(herb_name):
    """Maps actual herb names to known OCR hallucinations (from your original list)."""
    mapping = {
        "healing sunflower": ["sundlng", "hcalig", "healig", "sunllower", "sunllowe", "hcaling", "suadlag", "hlcaling", "hedig", "heali4g", "heallig", "ealv"],
        "black iron root": ["ionadoot", "bladz", "bonroor", "bouroot", "bladk", "kourooc", "bledk", "koro", "koroo", "bled", "korooz", "ko", "rooz"],
        "blue wave coral herb": ["ballaz", "coaileb", "ualheb", "oalhub", "blugwav", "blugwavg", "uallub", "qbal", "ualleb", "dallazz"],
        "thousand year lotus": ["hatsud", "yealoug", "yeaclos", "ibousand", "tbousand", "uouard", "iboutnd", "ycclas", "yac", "ibosseadd", "yatoud"],
        "moonlight jade leaf": ["saglui", "mopnlight", "meccligbt", "jadalzar", "jadeleal", "jadelea", "mooclight", "meonligbt", "jadglca", "saal", "meuuligbt", "saglti"],
        "ironbone grass": ["iobge", "kuboue", "ouboue", "bonbone", "konbong", "iabssa", "gcass", "iabge"],
        "wild spirit grass": ["budspide", "gas3", "wnika", "spinft", "eapnn"],
        "seven star flower": ["setcnsaac", "sevez", "sur", "8lst", "fte"],
        "cloud mist herb": ["candmse", "hedb", "dudsb", "hub"],
    }
    aliases = mapping.get(herb_name.lower(), [])
    # Add keywords from the name itself
    for w in herb_name.lower().split():
        if len(w) > 3: aliases.append(w)
    return list(set(aliases))

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    image = Image.open(image_file)
    img_array = np.array(image)
    
    # Scale for performance and accuracy
    h, w = img_array.shape[:2]
    scale = 1000 / w
    img_cv = cv2.resize(img_array, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    
    processed = preprocess_image(img_cv)
    results = reader.readtext(processed, text_threshold=0.3)
    
    curr_h, curr_w = processed.shape[:2]
    numbers_found = []
    herbs_found = []
    
    for bbox, text, prob in results:
        clean = text.lower().replace(' ', '')
        
        # 1. Number Interceptor (RegEx for 'x12', '22', etc.)
        clean_num = re.sub(r'[x|i|l|z|s|\|]', lambda m: {'x':'', 'i':'1', 'l':'1', 'z':'2', 's':'5', '|':'1'}.get(m.group(), ''), clean)
        nums = ''.join(filter(str.isdigit, clean_num))
        
        cx = (bbox[0][0] + bbox[1][0]) / 2
        cy = (bbox[0][1] + bbox[2][1]) / 2

        if nums and len(nums) <= 3:
            numbers_found.append({'qty': int(nums), 'x': cx, 'y': cy})
        else:
            # 2. Herb Matcher
            word = re.sub(r'[^a-z]', '', text.lower())
            if len(word) >= 3:
                matched_herb = None
                for herb in herb_list:
                    aliases = get_herb_aliases(herb)
                    # Check direct or fuzzy match
                    if word in aliases or difflib.get_close_matches(word, aliases, n=1, cutoff=0.75):
                        matched_herb = herb
                        break
                if matched_herb:
                    herbs_found.append({'herb': matched_herb, 'x': cx, 'y': cy})

    # PHASE 2: Geometry Relative Linker
    found_data = {}
    for h_frag in herbs_found:
        best_num = None
        min_dist = float('inf')
        for num in numbers_found:
            y_diff = num['y'] - h_frag['y']
            x_diff = abs(num['x'] - h_frag['x'])
            # Most game inventories put numbers slightly below or right of text
            if -20 < y_diff < (curr_h * 0.2) and x_diff < (curr_w * 0.15):
                dist = (x_diff**2 + y_diff**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    best_num = num
        if best_num:
            # Prevent overwriting with lower values if OCR sees duplicate items
            found_data[h_frag['herb']] = max(found_data.get(h_frag['herb'], 0), best_num['qty'])
            
    return found_data

# -------------------------------
# 2. FULL RECIPE DATABASE
# -------------------------------
def get_db():
    return {
        "Nine Yang Pill": [{"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92}, {"tier": "Heavenly", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "black iron root": 2, "crimson flame mushroom": 1}, "qi": 120}],
        "Jade Tide Pill": [{"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150}, {"tier": "Heavenly", "ingredients": {"blue wave coral herb": 2, "black iron root": 1, "crimson flame mushroom": 1, "bitter jade grass": 2}, "qi": 162}],
        "Stormheart Pill": [{"tier": "Heavenly", "ingredients": {"cloud mist herb": 4, "spirit spring herb": 2}, "qi": 225}],
        "Lotus Nirvana Pill": [{"tier": "Standard", "ingredients": {"thousand year lotus": 6}, "qi": 50}],
        "Starborn Agility Pill": [{"tier": "Imperfect", "ingredients": {"dandelion of qi": 1, "seven star flower": 2, "blue wave coral herb": 1, "cloud mist herb": 1, "spirit spring herb": 1}, "qi": 115}, {"tier": "Heavenly", "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230}],
        "Dragon Pulse Pill": [{"tier": "Heavenly (V1)", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 160}, {"tier": "Heavenly (V2)", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168}],
        "Void Clarity Pill": [{"tier": "Standard", "ingredients": {"starlight dew herb": 2, "cloud mist herb": 2, "heavenly spirit vine": 1, "bitter jade grass": 1}, "qi": 170}],
        "Celestial Harmony Pill": [{"tier": "Imperfect", "ingredients": {"silverleaf herb": 1, "seven star flower": 1, "mountain green herb": 1, "qi dandelion": 1, "wild spirit grass": 2}, "qi": 90}, {"tier": "Heavenly", "ingredients": {"thousand year lotus": 1, "silverleaf herb": 1, "seven star flower": 3, "moonlight jade leaf": 1}, "qi": 236}],
        "Seven Star Enlightenment": [{"tier": "Imperfect", "ingredients": {"spirit spring herb": 1, "seven star flower": 2, "starlight dew herb": 2, "silverleaf herb": 1}, "qi": 125}, {"tier": "Heavenly (Lotus)", "ingredients": {"thousand year lotus": 2, "blue wave coral herb": 1, "heavenly spirit vine": 1, "starlight dew herb": 2}, "qi": 285}, {"tier": "Heavenly (Pure)", "ingredients": {"heavenly spirit vine": 1, "starlight dew herb": 5}, "qi": 295}],
        "Dragon Essence Pill": [{"tier": "Standard", "ingredients": {"azure serpent grass": 1, "purple lightning orchid": 1, "nine suns flame grass": 1, "crimson flame mushroom": 2, "cloud mist herb": 1}, "qi": 0, "spec": "18% Lifespan"}, {"tier": "Heavenly", "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"}],
        "Sun Roses Rebirth": [{"tier": "Vit V1", "ingredients": {"wild bitter grass": 2, "red ginseng": 1, "healing sunflower": 2, "mountain green herb": 1}, "qi": 0, "spec": "20% Vitality (Perm)"}, {"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"}],
        "Ironclad Resolve": [{"tier": "Heavenly", "ingredients": {"silverleaf herb": 1, "moonlight jade leaf": 1, "spirit spring herb": 1, "crimson flame mushroom": 1, "black iron root": 2}, "qi": 0, "spec": "Perm Str/Vit"}],
    }

# -------------------------------
# 3. APP INTERFACE
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy", page_icon="🧿")

st.markdown("""<style>
    .stApp { background: #0e1117; }
    .card { background: #1c2128; border: 1px solid #30363d; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    .badge { background: #23863622; color: #3fb950; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 5px; }
    .ing-list { font-size: 0.85rem; color: #8b949e; margin-top: 10px; }
</style>""", unsafe_allow_html=True)

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

# Session State Init
for h in all_herbs:
    if f"i_{h}" not in st.session_state: st.session_state[f"i_{h}"] = 0

tab1, tab2 = st.tabs(["🥣 Alchemy Lab", "🎒 Storage"])

with tab2:
    st.header("Storage Management")
    c1, c2 = st.columns([2, 1])
    
    with c1:
        ss_file = st.file_uploader("Scan Inventory Screenshot", type=['png', 'jpg', 'jpeg'])
        if ss_file and st.button("✨ Auto-Update Chest"):
            with st.spinner("Decoding image..."):
                found = decompile_screenshot(ss_file, all_herbs)
                for h, q in found.items(): st.session_state[f"i_{h}"] = q
                st.success(f"Synced {len(found)} ingredients!")
                st.rerun()

    with c2:
        if st.button("🧹 Clear All"):
            for h in all_herbs: st.session_state[f"i_{h}"] = 0
            st.rerun()
        handcrafted = st.toggle("✨ Handcrafted (3x Qi Boost)", value=False)

    st.divider()
    h_search = st.text_input("Manual Filter...", "")
    cols = st.columns(4)
    for i, h in enumerate([hb for hb in all_herbs if h_search.lower() in hb]):
        with cols[i % 4]:
            st.number_input(h.title(), min_value=0, key=f"i_{h}")

with tab1:
    st.header("Available Recipes")
    p_query = st.text_input("Search Recipes (e.g. 'Vitality', 'Heavenly')...", "").lower()
    
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    
    for name, variants in db.items():
        for v in variants:
            # Calculation
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            
            if p_query and (p_query not in name.lower() and p_query not in v.get('spec', '').lower()):
                continue

            with st.container():
                st.markdown(f"""<div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <small style="color:#58a6ff">{v['tier']}</small>
                            <h3 style="margin:0;">{name}</h3>
                        </div>
                        <div style="text-align:right">
                            <small>BATCHABLE</small><br><span style="font-size:1.5rem; color:#58a6ff; font-weight:bold;">{amt}</span>
                        </div>
                    </div>
                    <div style="margin: 8px 0;">
                        <span class="badge">+{v['qi'] * (3 if handcrafted else 1)}% Qi</span>
                        {f'<span class="badge" style="color:#d2a8ff; background:#8957e522;">{v["spec"]}</span>' if v.get("spec") else ""}
                    </div>
                </div>""", unsafe_allow_html=True)
                
                # Ingredient visualization
                ing_cols = st.columns(len(v["ingredients"]))
                for idx, (ing, req) in enumerate(v["ingredients"].items()):
                    has = inv.get(ing, 0)
                    color = "#3fb950" if has >= req else "#f85149"
                    ing_cols[idx].markdown(f"<div class='ing-list'>{ing.title()}<br><b style='color:{color}'>{has}/{req}</b></div>", unsafe_allow_html=True)
                
                if amt > 0:
                    if st.button(f"Craft 1x {name}", key=f"btn_{name}_{v['tier']}"):
                        for ing, req in v["ingredients"].items():
                            st.session_state[f"i_{ing}"] -= req
                        st.toast(f"Produced 1x {name}!")
                        st.rerun()
                st.divider()
