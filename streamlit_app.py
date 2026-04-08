import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import difflib
import re

# -------------------------------
# 1. THE INVERSE SILHOUETTE ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

def get_herb_aliases(herb_name):
    """Unified Hallucination Dictionary"""
    aliases = []
    mapping = {
        "healing sunflower": ["healing", "sunflower", "sundlng", "hcalig", "suadlag", "hlcaling", "sannhg", "sunllower"],
        "black iron root": ["black", "ironroot", "ionadoot", "bladz", "bonroor", "bouroot", "bladk", "kourooc", "bledk", "koroo", "koro", "iecat"],
        "blue wave coral herb": ["blue", "wave", "coral", "ballaz", "coaileb", "ualheb", "blugwav", "uallub", "qbal", "dallazz", "sazglxb"],
        "thousand year lotus": ["thousand", "lotus", "hatsud", "yealoug", "yeaclos", "ibousand", "tbousand", "uouard", "iboutnd", "ycclas", "yatoud", "yac"],
        "moonlight jade leaf": ["moonlight", "jadeleaf", "saglui", "mopnlight", "meccligbt", "jadalzar", "jadeleal", "jadelea", "mooclight", "meonligbt", "jadglca", "saal", "saglti", "8na3z"],
        "ironbone grass": ["ironbone", "gtass", "iobge", "kuboue", "ouboue", "bonbone", "konbong", "iabssa", "gcass", "iabge", "laza", "otz"],
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
        "wild bitter grass": ["wildbitter", "bittergrass"]
    }
    if herb_name.lower() in mapping:
        aliases.extend(mapping[herb_name.lower()])
    for w in herb_name.lower().split():
        if len(w) > 3: aliases.append(w)
    return list(set(aliases))

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # ⚡ SMART SCALING
    h, w = img_cv.shape[:2]
    scale = 1000 / w
    img_cv = cv2.resize(img_cv, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    
    # 🧪 ADVANCED PRE-PROCESSING (Silhouette Edge Detection)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    kernel = np.ones((2,2), np.uint8)
    # Morphological gradient helps 'thicken' the thin white game font
    gradient = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
    # Otsu's thresholding automatically finds the best contrast
    _, processed = cv2.threshold(gradient, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Run OCR on the Edge-Detected image
    results = reader.readtext(processed, text_threshold=0.3)
    
    curr_h, curr_w = processed.shape[:2]
    numbers_found = []
    herbs_found = []
    raw_text_seen = []
    
    for bbox, text, prob in results:
        raw_text_seen.append(text)
        clean = text.lower().replace(' ', '')
        
        # Intercept double-digit glitches
        if clean in ['22', 'z2', 'x2z']: clean = 'x2'
        if clean in ['12', 'xz', 'xlz', 'xiz']: clean = 'x12'
        
        clean = clean.replace('i', '1').replace('|', '1').replace('l', '1').replace('s', '5').replace('o', '0')
        
        cx = (bbox[0][0] + bbox[1][0]) / 2
        cy = (bbox[0][1] + bbox[2][1]) / 2
        
        if ('x' in clean or any(c.isdigit() for c in clean)) and len(clean) < 6:
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
                        if len(alias) > 3 and difflib.SequenceMatcher(None, word, alias).ratio() > 0.70:
                            matched_herb = herb
                            break
                    if matched_herb: break
                if matched_herb:
                    herbs_found.append({'herb': matched_herb, 'x': cx, 'y': cy})

    # PHASE 2: Geometric Mapping
    found_data = {}
    for h_frag in herbs_found:
        best_num = None
        min_dist = float('inf')
        for num in numbers_found:
            y_diff = h_frag['y'] - num['y']
            x_diff = abs(h_frag['x'] - num['x'])
            if 0 < y_diff < (curr_h * 0.25) and x_diff < (curr_w * 0.12):
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
# 2. FULL RECIPE DATABASE
# -------------------------------
def get_db():
    return {
        "Nine Yang Pill": [{"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92}, {"tier": "Heavenly", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "black iron root": 2, "crimson flame mushroom": 1}, "qi": 120}],
        "Jade Tide Pill": [{"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150}, {"tier": "Heavenly", "ingredients": {"blue wave coral herb": 2, "black iron root": 1, "crimson flame mushroom": 1, "bitter jade grass": 2}, "qi": 162}],
        "Stormheart Pill": [{"tier": "Heavenly", "ingredients": {"cloud mist herb": 4, "spirit spring herb": 2}, "qi": 225}],
        "Lotus Nirvana Pill": [{"tier": "Standard", "ingredients": {"thousand year lotus": 6}, "qi": 50}],
        "Starborn Agility Pill": [{"tier": "Imperfect", "ingredients": {"dandelion of qi": 1, "seven star flower": 2, "blue wave coral herb": 1, "cloud mist herb": 1, "spirit spring herb": 1}, "qi": 115}, {"tier": "Heavenly", "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230}],
        "Dragon Pulse Pill": [{"tier": "Imperfect", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 80}, {"tier": "Heavenly (V1)", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 160}, {"tier": "Heavenly (V2)", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168}],
        "Void Clarity Pill": [{"tier": "Standard", "ingredients": {"starlight dew herb": 2, "cloud mist herb": 2, "heavenly spirit vine": 1, "bitter jade grass": 1}, "qi": 170}],
        "Celestial Harmony Pill": [{"tier": "Imperfect", "ingredients": {"silverleaf herb": 1, "seven star flower": 1, "mountain green herb": 1, "qi dandelion": 1, "wild spirit grass": 2}, "qi": 90}, {"tier": "Heavenly", "ingredients": {"thousand year lotus": 1, "silverleaf herb": 1, "seven star flower": 3, "moonlight jade leaf": 1}, "qi": 236}],
        "Seven Star Enlightenment": [{"tier": "Imperfect", "ingredients": {"spirit spring herb": 1, "seven star flower": 2, "starlight dew herb": 2, "silverleaf herb": 1}, "qi": 125}, {"tier": "Heavenly (Lotus)", "ingredients": {"thousand year lotus": 2, "blue wave coral herb": 1, "heavenly spirit vine": 1, "starlight dew herb": 2}, "qi": 285}, {"tier": "Heavenly (Pure)", "ingredients": {"heavenly spirit vine": 1, "starlight dew herb": 5}, "qi": 295}],
        "Dragon Essence Pill": [{"tier": "Standard", "ingredients": {"azure serpent grass": 1, "purple lightning orchid": 1, "nine suns flame grass": 1, "crimson flame mushroom": 2, "cloud mist herb": 1}, "qi": 0, "spec": "18% Lifespan"}, {"tier": "Heavenly", "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"}],
        "Sun Roses Rebirth": [{"tier": "Vit V1", "ingredients": {"wild bitter grass": 2, "red ginseng": 1, "healing sunflower": 2, "mountain green herb": 1}, "qi": 0, "spec": "20% Vitality (Perm)"}, {"tier": "Vit V2", "ingredients": {"mountain green herb": 3, "healing sunflower": 3}, "qi": 0, "spec": "20% Vitality (Perm)"}, {"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"}, {"tier": "Vit V4", "ingredients": {"healing sunflower": 2, "ironbone grass": 3, "red ginseng": 1}, "qi": 0, "spec": "41% Vitality (Perm)"}],
        "Phoenix Ember Pill": [{"tier": "Standard", "ingredients": {"crimson flame mushroom": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 2, "spirit spring herb": 1}, "qi": 0, "spec": "70% Vit / 40% Spd"}],
        "Mistveil Focus Pill": [{"tier": "Standard", "ingredients": {"silverleaf herb": 3, "spirit spring herb": 3}, "qi": 238}, {"tier": "Focus-V2", "ingredients": {"silverleaf herb": 3, "spirit spring herb": 2, "seven star flower": 1}, "qi": 245}, {"tier": "Focus-V3", "ingredients": {"cloud mist herb": 2, "spirit spring herb": 2, "starlight dew herb": 1, "heavenly spirit vine": 1}, "qi": 260}],
        "Concentration Pill": [{"tier": "Dandelion Mix", "ingredients": {"seven star flower": 1, "azure serpent grass": 3, "dandelion of qi": 2}, "qi": 100}, {"tier": "Pure Mix", "ingredients": {"seven star flower": 3, "azure serpent grass": 3}, "qi": 100}, {"tier": "Spring Mix", "ingredients": {"seven star flower": 1, "azure serpent grass": 3, "spirit spring herb": 2}, "qi": 100}],
        "Ironclad Resolve": [{"tier": "Heavenly", "ingredients": {"silverleaf herb": 1, "moonlight jade leaf": 1, "spirit spring herb": 1, "crimson flame mushroom": 1, "black iron root": 2}, "qi": 0, "spec": "Perm Str/Vit"}],
        "Tideborn Vigor": [{"tier": "Heavenly", "ingredients": {"wild spirit grass": 1, "wild bitter grass": 1, "red ginseng": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 1}, "qi": 0, "spec": "Vit/Str Boost"}],
        "Blazewind Pill": [{"tier": "Heavenly", "ingredients": {"crimson flame mushroom": 2, "purple lightning orchid": 3, "wild spirit grass": 1}, "qi": 0, "spec": "Perm Spd/Str"}],
        "Soul Replenishing": [{"tier": "Heavenly", "ingredients": {"healing sunflower": 2, "red ginseng": 1, "ironbone grass": 2, "seven star flower": 1}, "qi": 0, "spec": "12% Lifespan (Perm)"}]
    }

# -------------------------------
# 3. APP STYLING & INIT
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

st.markdown("""<style>
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
    header {visibility: hidden;} footer {visibility: hidden;}
    .stTabs [data-baseweb="tab"] { background-color: rgba(255, 255, 255, 0.05); color: #8b949e; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: rgba(88, 166, 255, 0.15) !important; color: #58a6ff !important; border-bottom: 2px solid #58a6ff !important; }
    label { color: #f0f6fc !important; font-weight: 600 !important; }
    div[data-baseweb="input"] { background-color: rgba(0, 0, 0, 0.4) !important; border: 1px solid rgba(88, 166, 255, 0.3) !important; border-radius: 8px !important; }
    .app-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border-radius: 15px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px; color: white; }
    .pill-title { color: #58a6ff; font-size: 1.3rem; font-weight: bold; margin: 0; }
    .badge { display: inline-block; background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; margin-top: 5px; border: 1px solid rgba(88, 166, 255, 0.2); }
    .total-box { margin-top: 12px; padding: 10px; background: rgba(0, 0, 0, 0.3); border-radius: 10px; border: 1px dashed rgba(88, 166, 255, 0.2); }
</style>""", unsafe_allow_html=True)

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

for h in all_herbs:
    if f"i_{h}" not in st.session_state: 
        st.session_state[f"i_{h}"] = 0

if 'debug_log' not in st.session_state:
    st.session_state['debug_log'] = []

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

with tab2:
    st.markdown("### 📸 Visual Decompiler")
    ss_file = st.file_uploader("Upload Inventory Screenshot", type=['png', 'jpg', 'jpeg'])
    
    if ss_file:
        if st.button("✨ Decompile Image"):
            with st.spinner("Decoding Herbs..."):
                found, raw_text = decompile_screenshot(ss_file, all_herbs)
                st.session_state['debug_log'] = raw_text
                if found:
                    for herb, qty in found.items(): 
                        st.session_state[f"i_{herb}"] += qty
                    st.success(f"Added {len(found)} herbs to chest!")
                    st.rerun()
                else: 
                    st.error("No herbs detected. Try a closer crop of the selection window.")

    if st.session_state['debug_log']:
        with st.expander("🛠️ View Raw AI Data (Debug)"):
            st.write(st.session_state['debug_log'])

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Clear All Stock"):
            for h in all_herbs: st.session_state[f"i_{h}"] = 0
            st.session_state['debug_log'] = []
            st.rerun()
    with c2: 
        handcrafted = st.toggle("✨ Handcrafted (3x)", value=False)
    
    h_search = st.text_input("🔍 Search Inventory...", "").lower()
    cols = st.columns(2)
    filtered = [h for h in all_herbs if h_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 2]: 
            st.number_input(h.title(), min_value=0, key=f"i_{h}")

with tab1:
    p_query = st.text_input("🔍 Live Search Recipes...", "").lower()
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    craftable = []
    
    for name, variants in db.items():
        for v in variants:
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            if amt > 0:
                qi_val = v["qi"] * 3 if handcrafted else v["qi"]
                if not p_query or p_query in name.lower() or p_query in v.get('spec', '').lower() or p_query in v['tier'].lower():
                    craftable.append({"name": name, "tier": v["tier"], "amt": amt, "qi": qi_val, "spec": v.get("spec"), "ing": v["ingredients"]})

    if craftable:
        for p in sorted(craftable, key=lambda x: x['qi'], reverse=True):
            is_perm = any(w in (p['spec'] or "").lower() for w in ["perm", "lifespan", "nirvana"])
            tags = f'<span style="background:rgba(255,255,255,0.1); color:white; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-right:4px;">{"Permanent" if is_perm else "Temporary"}</span>'
            if p['qi'] > 0: tags += f'<span style="background:rgba(63,185,80,0.2); color:#3fb950; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-right:4px;">+{p["qi"]}% Qi</span>'
            if p['spec']:
                for s in p['spec'].split('/'): tags += f'<span style="background:rgba(187,128,255,0.2); color:#d2a8ff; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-right:4px;">{s.strip()}</span>'
            badges = "".join([f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in p["ing"].items()])
            totals = "".join([f'<div style="font-size: 0.8rem; margin-bottom:2px;">• {ing.title()}: <b>{req*p["amt"]}</b></div>' for ing, req in p["ing"].items()])
            st.markdown(f"""<div class="app-card">
                <div style="display:flex; justify-content:space-between;">
                    <div><div style="color:#8b949e; font-size:0.7rem;">{p['tier']}</div><div class="pill-title">{p['name']}</div><div style="margin-top:4px;">{tags}</div></div>
                    <div style="text-align:right;"><div style="font-size:0.6rem; color:#8b949e;">BATCH</div><div style="font-size:1.8rem; color:#58a6ff; font-weight:bold;">{p['amt']}</div></div>
                </div>
                <div style="margin-top:10px;">{badges}</div>
                <div class="total-box"><b>BATCH MATERIALS:</b><br>{totals}</div>
            </div>""", unsafe_allow_html=True)
    else: 
        st.info("No craftable items. Scan a screenshot or add ingredients manually.")
