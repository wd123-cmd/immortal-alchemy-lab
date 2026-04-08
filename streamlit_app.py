import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image
import difflib
import re

# -------------------------------
# 1. CORE ENGINE (OCR & VISION)
# -------------------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

def get_herb_aliases(herb_name):
    mapping = {
        "healing sunflower": ["sundlng", "hcalig", "healig", "sunllower", "hcaling", "suadlag", "hedig"],
        "black iron root": ["ionadoot", "bladz", "bonroor", "bouroot", "bladk", "kourooc", "koroo", "bled"],
        "blue wave coral herb": ["ballaz", "coaileb", "ualheb", "oalhub", "blugwav", "uallub", "qbal"],
        "thousand year lotus": ["hatsud", "yealoug", "yeaclos", "ibousand", "tbousand", "uouard"],
        "moonlight jade leaf": ["saglui", "mopnlight", "meccligbt", "jadalzar", "jadeleal", "mooclight"],
        "ironbone grass": ["iobge", "kuboue", "ouboue", "bonbone", "konbong", "iabssa", "gcass"],
        "wild spirit grass": ["budspide", "gas3", "wnika", "spinft", "eapnn"],
        "seven star flower": ["setcnsaac", "sevez", "sur", "8lst", "fte"]
    }
    aliases = mapping.get(herb_name.lower(), [])
    for w in herb_name.lower().split():
        if len(w) > 3: aliases.append(w)
    return list(set(aliases))

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    scale = 800 / img_cv.shape[1]
    img_cv = cv2.resize(img_cv, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    results = reader.readtext(gray, text_threshold=0.2, low_text=0.2)
    curr_h, curr_w = gray.shape[:2]
    numbers_found, herbs_found = [], []
    
    for bbox, text, prob in results:
        clean = text.lower().replace(' ', '')
        # OCR Correction Logic
        clean = clean.replace('xz', 'x12').replace('xlz', 'x12').replace('xiz', 'x12')
        for c, r in [('i','1'), ('|','1'), ('l','1'), ('s','5'), ('o','0'), ('z','2')]: clean = clean.replace(c, r)
        
        cx, cy = (bbox[0][0] + bbox[1][0]) / 2, (bbox[0][1] + bbox[2][1]) / 2
        
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

    found_inv = {}
    for h_frag in herbs_found:
        best_num, min_dist = None, float('inf')
        for num in numbers_found:
            y_diff, x_diff = h_frag['y'] - num['y'], abs(h_frag['x'] - num['x'])
            if 0 < y_diff < (curr_h * 0.3) and x_diff < (curr_w * 0.15):
                dist = (x_diff**2 + y_diff**2)**0.5
                if dist < min_dist: min_dist, best_num = dist, num
        if best_num: found_inv[h_frag['herb']] = max(found_inv.get(h_frag['herb'], 0), best_num['qty'])
    return found_inv

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
        "Dragon Pulse Pill": [{"tier": "Heavenly (V1)", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 160}],
        "Dragon Essence Pill": [{"tier": "Standard", "ingredients": {"azure serpent grass": 1, "purple lightning orchid": 1, "nine suns flame grass": 1, "crimson flame mushroom": 2, "cloud mist herb": 1}, "qi": 0, "spec": "18% Lifespan"}, {"tier": "Heavenly", "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"}],
        "Sun Roses Rebirth": [{"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"}],
        "Ironclad Resolve": [{"tier": "Heavenly", "ingredients": {"silverleaf herb": 1, "moonlight jade leaf": 1, "spirit spring herb": 1, "crimson flame mushroom": 1, "black iron root": 2}, "qi": 0, "spec": "Perm Str/Vit"}],
    }

# -------------------------------
# 3. INTERFACE & STATE MANAGEMENT
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy", page_icon="🧿")

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

# --- CRITICAL FIX: Decoupled State ---
if 'inventory' not in st.session_state:
    st.session_state.inventory = {h: 0 for h in all_herbs}

def update_inv(herb, val):
    st.session_state.inventory[herb] = val

st.markdown("""<style>
    .stApp { background: #0e1117; color: white; }
    .app-card { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1.2rem; border: 1px solid rgba(88, 166, 255, 0.2); margin-bottom: 1rem; }
    .pill-title { color: #58a6ff; font-size: 1.4rem; font-weight: bold; margin: 0; }
    .badge { display: inline-block; background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; border: 1px solid rgba(88, 166, 255, 0.2); margin-right: 5px; }
</style>""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

# --- TAB 2: INVENTORY ---
with tab2:
    st.markdown("### 📸 Screenshot Decompiler")
    ss_file = st.file_uploader("Upload Inventory Screenshot", type=['png', 'jpg', 'jpeg'])
    if ss_file and st.button("✨ Decompile Image"):
        with st.spinner("Decoding patterns..."):
            found = decompile_screenshot(ss_file, all_herbs)
            for h, q in found.items():
                st.session_state.inventory[h] = q
            st.success("Chest Updated!")
            st.rerun()

    c1, c2 = st.columns(2)
    with c1: 
        if st.button("🧹 Clear All Stock"):
            st.session_state.inventory = {h: 0 for h in all_herbs}
            st.rerun()
    with c2: handcrafted = st.toggle("✨ Handcrafted (3x)", value=False)

    h_search = st.text_input("🔍 Manual Search/Edit...", "").lower()
    cols = st.columns(3)
    filtered = [h for h in all_herbs if h_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 3]:
            # Use 'value' instead of 'key' to avoid modification errors
            new_val = st.number_input(h.title(), min_value=0, value=st.session_state.inventory[h], key=f"widget_{h}")
            st.session_state.inventory[h] = new_val

# --- TAB 1: BREWING ---
with tab1:
    p_query = st.text_input("🔍 Search Recipes...", "").lower()
    
    for name, variants in db.items():
        for v in variants:
            # Check availability using the internal dict
            possible = [st.session_state.inventory.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            
            if amt > 0 and (not p_query or p_query in name.lower() or p_query in v['tier'].lower()):
                qi_val = v["qi"] * 3 if handcrafted else v["qi"]
                is_perm = any(w in (v.get('spec', '')).lower() for w in ["perm", "lifespan"])
                
                badge_html = f'<span class="badge">{"Permanent" if is_perm else "Temporary"}</span>'
                if qi_val > 0: badge_html += f'<span class="badge" style="color:#3fb950;">+{qi_val}% Qi</span>'
                if v.get("spec"): badge_html += f'<span class="badge" style="color:#d2a8ff;">{v["spec"]}</span>'

                st.markdown(f'''
<div class="app-card">
    <div style="display:flex; justify-content:space-between; align-items: flex-start;">
        <div>
            <div style="color:#8b949e; font-size:0.75rem;">{v['tier']} Variant</div>
            <div class="pill-title">{name}</div>
            <div style="margin-top:8px;">{badge_html}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:0.65rem; color:#8b949e; text-transform:uppercase;">Can Craft</div>
            <div style="font-size:1.8rem; color:#58a6ff; font-weight:bold; line-height:1;">{amt}</div>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)
                
                if st.button(f"Brew 1x {name} ({v['tier']})", key=f"btn_{name}_{v['tier']}"):
                    # Modify the internal dict, not the widget key directly
                    for ing, req in v["ingredients"].items():
                        st.session_state.inventory[ing] -= req
                    st.toast(f"Produced 1x {name}!")
                    st.rerun()
                st.divider()

    if not any(st.session_state.inventory.get(ing, 0) >= req for name in db for v in db[name] for ing, req in v["ingredients"].items()):
        st.info("No craftable items found. Scan a screenshot or add ingredients to the chest.")
