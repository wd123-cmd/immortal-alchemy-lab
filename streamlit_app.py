import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import difflib
import re

# -------------------------------
# 1. SETTINGS & OCR ENGINE
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

@st.cache_resource
def load_ocr():
    """Initializes the EasyOCR Reader."""
    return easyocr.Reader(['en'], gpu=False)

def get_herb_aliases(herb_name):
    """Maps actual herb names to known OCR hallucinations and fragments."""
    mapping = {
        "healing sunflower": ["healing", "sunflower", "sundlng", "hcalig", "healig", "sunllower", "sunllowe", "hcaling", "suadlag", "hlcaling", "hedig", "heali4g", "heallig", "ealv"],
        "black iron root": ["black", "ironroot", "ionadoot", "bladz", "bonroor", "bouroot", "bladk", "kourooc", "bledk", "koro", "koroo", "bled", "korooz", "ko", "rooz"],
        "blue wave coral herb": ["blue", "wave", "coral", "ballaz", "coaileb", "ualheb", "oalhub", "blugwav", "blugwavg", "uallub", "qbal", "ualleb", "dallazz"],
        "thousand year lotus": ["thousand", "lotus", "hatsud", "yealoug", "yeaclos", "ibousand", "tbousand", "uouard", "iboutnd", "ycclas", "yac", "ibosseadd", "yatoud"],
        "moonlight jade leaf": ["moonlight", "jadeleaf", "saglui", "mopnlight", "meccligbt", "jadalzar", "jadeleal", "jadelea", "mooclight", "meonligbt", "jadglca", "saal", "meuuligbt", "saglti"],
        "ironbone grass": ["ironbone", "gtass", "iobge", "kuboue", "ouboue", "bonbone", "konbong", "iabssa", "gcass", "iabge"],
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
    aliases = mapping.get(herb_name.lower(), [])
    # Dynamic splitting to catch single words
    for w in herb_name.lower().split():
        if len(w) > 3: aliases.append(w)
    return list(set(aliases))

def decompile_screenshot(image_file, herb_list):
    """Processes image and matches text blocks to quantities via geometry."""
    reader = load_ocr()
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # --- ⚡ SPEED SCALING (User Preference: 800px) ---
    h_orig, w_orig = img_cv.shape[:2]
    scale = 800 / w_orig
    img_cv = cv2.resize(img_cv, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray, text_threshold=0.2, low_text=0.2)
    
    curr_h, curr_w = gray.shape[:2]
    numbers_found, herbs_found, raw_text_seen = [], [], []
    
    for bbox, text, prob in results:
        raw_text_seen.append(text)
        clean = text.lower().replace(' ', '')
        
        # --- 🚨 THE DOUBLE-DIGIT NUMBER INTERCEPTOR 🚨 ---
        clean = clean.replace('xz', 'x12').replace('xlz', 'x12').replace('xiz', 'x12').replace('x2z', 'x12')
        clean = clean.replace('xi2', 'x12').replace('x|2', 'x12').replace('xl2', 'x12').replace('x22', 'x12')
        if clean in ['22', '44', '55']: clean = 'x' + clean[0]
        
        # Character swapping for common OCR errors
        for char, replacement in [('i', '1'), ('|', '1'), ('l', '1'), ('s', '5'), ('o', '0'), ('z', '2')]:
            clean = clean.replace(char, replacement)
        
        cx = (bbox[0][0] + bbox[1][0]) / 2
        cy = (bbox[0][1] + bbox[2][1]) / 2
        
        if ('x' in clean or any(c.isdigit() for c in clean)) and len(clean) < 6:
            nums = ''.join(filter(str.isdigit, clean))
            if nums: numbers_found.append({'qty': int(nums), 'x': cx, 'y': cy})
        else:
            word = re.sub(r'[^a-z]', '', text.lower())
            if len(word) >= 3:
                for herb in herb_list:
                    aliases = get_herb_aliases(herb)
                    if word in aliases or any(difflib.SequenceMatcher(None, word, a).ratio() > 0.75 for a in aliases):
                        herbs_found.append({'herb': herb, 'x': cx, 'y': cy})
                        break

    # PHASE 2: Geometry Linking
    found_data = {}
    max_y_dist, max_x_dist = curr_h * 0.3, curr_w * 0.15
    
    for h_frag in herbs_found:
        best_num, min_dist = None, float('inf')
        for num in numbers_found:
            y_diff = h_frag['y'] - num['y']
            x_diff = abs(h_frag['x'] - num['x'])
            if 0 < y_diff < max_y_dist and x_diff < max_x_dist:
                dist = (x_diff**2 + y_diff**2)**0.5
                if dist < min_dist:
                    min_dist, best_num = dist, num
        if best_num:
            herb = h_frag['herb']
            found_data[herb] = max(found_data.get(herb, 0), best_num['qty'])
                
    return found_data, raw_text_seen

# -------------------------------
# 2. RECIPE DATABASE
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
# 3. UI & STATE
# -------------------------------
st.markdown("""<style>
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); color: white; }
    header {visibility: hidden;} .stTabs [data-baseweb="tab"] { color: #8b949e; }
    .app-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 12px; padding: 15px; border: 1px solid rgba(88, 166, 255, 0.2); margin-bottom: 12px; }
    .pill-title { color: #58a6ff; font-size: 1.2rem; font-weight: bold; }
    .badge { display: inline-block; background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 5px; border: 1px solid rgba(88, 166, 255, 0.2); }
</style>""", unsafe_allow_html=True)

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

# Session State
for h in all_herbs:
    if f"i_{h}" not in st.session_state: st.session_state[f"i_{h}"] = 0
if 'debug_log' not in st.session_state: st.session_state['debug_log'] = []

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

# --- TAB 2: INVENTORY ---
with tab2:
    st.markdown("### 📸 Visual Decompiler")
    ss_file = st.file_uploader("Upload Inventory Screenshot", type=['png', 'jpg', 'jpeg'])
    if ss_file and st.button("✨ Decompile Image"):
        with st.spinner("Raycasting Layout..."):
            found, raw = decompile_screenshot(ss_file, all_herbs)
            st.session_state['debug_log'] = raw
            if found:
                for h, q in found.items(): st.session_state[f"i_{h}"] = q
                st.success("Chest Updated!")
                st.rerun()

    if st.session_state['debug_log']:
        with st.expander("🛠️ Debug Raw Data"): st.write(st.session_state['debug_log'])

    st.divider()
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("🧹 Clear Stock"):
            for h in all_herbs: st.session_state[f"i_{h}"] = 0
            st.rerun()
    with c2: handcrafted = st.toggle("✨ Handcrafted (3x)", value=False)

    h_search = st.text_input("🔍 Manual Adjust...", "").lower()
    cols = st.columns(3)
    filtered = [h for h in all_herbs if h_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 3]: st.number_input(h.title(), min_value=0, key=f"i_{h}")

# --- TAB 1: CRAFTING ---
with tab1:
    p_query = st.text_input("🔍 Search Recipes...", "").lower()
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    
    for name, variants in db.items():
        for v in variants:
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            
            if amt > 0 and (not p_query or p_query in name.lower() or p_query in v['tier'].lower()):
                qi_val = v["qi"] * 3 if handcrafted else v["qi"]
                is_perm = any(w in (v.get('spec', '')).lower() for w in ["perm", "lifespan"])
                
                st.markdown(f"""<div class="app-card">
                    <div style="display:flex; justify-content:space-between;">
                        <div>
                            <div style="color:#8b949e; font-size:0.7rem;">{v['tier']}</div>
                            <div class="pill-title">{name}</div>
                            <div style="margin-top:5px;">
                                <span class="badge">{"Permanent" if is_perm else "Temporary"}</span>
                                {f'<span class="badge" style="color:#3fb950;">+{qi_val}% Qi</span>' if qi_val > 0 else ''}
                                {f'<span class="badge" style="color:#d2a8ff;">{v.get("spec", "")}</span>' if v.get("spec") else ''}
                            </div>
                        </div>
                        <div style="text-align:right;"><small>BATCH</small><br><b style="font-size:1.5rem; color:#58a6ff;">{amt}</b></div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                if st.button(f"Consume Materials for 1x {name} ({v['tier']})", key=f"btn_{name}_{v['tier']}"):
                    for ing, req in v["ingredients"].items():
                        st.session_state[f"i_{ing}"] -= req
                    st.toast(f"Produced {name}!")
                    st.rerun()
                st.divider()
