import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image

# -------------------------------
# 1. MULTI-STAGE DECOMPILER ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # --- MULTI-STAGE PRE-PROCESSING ---
    # Filter A: Original Color
    # Filter B: Grayscale + High Contrast
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    contrast = cv2.convertScaleAbs(gray, alpha=2.0, beta=0)
    # Filter C: Dilation (Thickens the thin 'x12' font)
    kernel = np.ones((2,2), np.uint8)
    dilated = cv2.dilate(contrast, kernel, iterations=1)
    
    # Run OCR on all versions to maximize detection chances
    results = reader.readtext(img_cv) + reader.readtext(contrast) + reader.readtext(dilated)
    
    # Sort results by vertical position (Top to Bottom)
    results.sort(key=lambda x: x[0][0][1])

    found_data = {}
    for i, (bbox, text, prob) in enumerate(results):
        # CLEAN & CORRECT FONT ERRORS
        clean = text.lower().replace(' ', '')
        clean = clean.replace('i', '1').replace('|', '1').replace('l', '1').replace('[', '1')
        clean = clean.replace('s', '5').replace('o', '0').replace('q', '9').replace('z', '2').replace('g', '9')
        
        # Identify Quantity (looking for numbers)
        num_str = ''.join(filter(str.isdigit, clean))
        if num_str and len(num_str) < 5:
            try:
                quantity = int(num_str)
                
                # SEARCH NEARBY: Look at 5 text blocks around the number
                for j in range(-2, 5): 
                    if 0 <= i + j < len(results):
                        potential_name = results[i+j][1].lower().strip()
                        for herb in herb_list:
                            # Fuzzy check: If herb name is inside the read text or vice versa
                            if herb.lower() in potential_name or potential_name in herb.lower():
                                # Only update if we found a higher quantity (prevents double-counting)
                                if herb not in found_data or quantity > found_data[herb]:
                                    found_data[herb] = quantity
                                break
            except: continue
            
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
        "Starborn Agility Pill": [{"tier": "Heavenly", "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230}],
        "Dragon Pulse Pill": [{"tier": "Heavenly (V2)", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168}],
        "Void Clarity Pill": [{"tier": "Standard", "ingredients": {"starlight dew herb": 2, "cloud mist herb": 2, "heavenly spirit vine": 1, "bitter jade grass": 1}, "qi": 170}],
        "Celestial Harmony Pill": [{"tier": "Heavenly", "ingredients": {"thousand year lotus": 1, "silverleaf herb": 1, "seven star flower": 3, "moonlight jade leaf": 1}, "qi": 236}],
        "Seven Star Enlightenment": [{"tier": "Heavenly (Pure)", "ingredients": {"heavenly spirit vine": 1, "starlight dew herb": 5}, "qi": 295}],
        "Dragon Essence Pill": [{"tier": "Heavenly", "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"}],
        "Sun Roses Rebirth": [{"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"}],
        "Phoenix Ember Pill": [{"tier": "Standard", "ingredients": {"crimson flame mushroom": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 2, "spirit spring herb": 1}, "qi": 0, "spec": "70% Vit / 40% Spd"}],
        "Mistveil Focus Pill": [{"tier": "Focus-V3", "ingredients": {"cloud mist herb": 2, "spirit spring herb": 2, "starlight dew herb": 1, "heavenly spirit vine": 1}, "qi": 260}],
        "Ironclad Resolve": [{"tier": "Heavenly", "ingredients": {"silverleaf herb": 1, "moonlight jade leaf": 1, "spirit spring herb": 1, "crimson flame mushroom": 1, "black iron root": 2}, "qi": 0, "spec": "Perm Str/Vit"}],
        "Blazewind Pill": [{"tier": "Heavenly", "ingredients": {"crimson flame mushroom": 2, "purple lightning orchid": 3, "wild spirit grass": 1}, "qi": 0, "spec": "Perm Spd/Str"}],
        "Soul Replenishing": [{"tier": "Heavenly", "ingredients": {"healing sunflower": 2, "red ginseng": 1, "ironbone grass": 2, "seven star flower": 1}, "qi": 0, "spec": "12% Lifespan (Perm)"}]
    }

# -------------------------------
# 3. APP STYLING & STATE
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
    if f"i_{h}" not in st.session_state: st.session_state[f"i_{h}"] = 0

# -------------------------------
# 4. MAIN INTERFACE
# -------------------------------
tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

with tab2:
    st.markdown("### 📸 Visual Reader")
    ss_file = st.file_uploader("Upload Inventory Screenshot", type=['png', 'jpg', 'jpeg'])
    if ss_file:
        if st.button("✨ Decompile Image"):
            with st.spinner("Decoding Spirit Herbs..."):
                found = decompile_screenshot(ss_file, all_herbs)
                if found:
                    for herb, qty in found.items(): st.session_state[f"i_{herb}"] = qty
                    st.success(f"Successfully decoded {len(found)} herbs!")
                    st.rerun()
                else: st.error("Reader failed. Make sure numbers and names are visible.")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Clear All Stock"):
            for h in all_herbs: st.session_state[f"i_{h}"] = 0
            st.rerun()
    with c2: handcrafted = st.toggle("✨ Handcrafted (3x)", value=False)
    
    h_search = st.text_input("🔍 Manual Search/Edit...", "").lower()
    cols = st.columns(2)
    filtered = [h for h in all_herbs if h_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 2]: st.number_input(h.title(), min_value=0, key=f"i_{h}")

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
    else: st.info("No craftable items. Scan a screenshot or add ingredients in the next tab.")
