import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image

# -------------------------------
# 1. ENHANCED DECOMPILER ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'])

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    
    # Load and convert to OpenCV format
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # PRE-PROCESSING: High Contrast & Grayscale (Helps read the 'x12' font)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    # Increase contrast to make the white text pop against dark backgrounds
    enhanced = cv2.convertScaleAbs(gray, alpha=1.5, beta=0) 
    
    results = reader.readtext(enhanced)
    
    found_data = {}
    
    # Search logic
    for i, (bbox, text, prob) in enumerate(results):
        # Clean text: remove spaces, lowercase, handle common OCR errors
        clean_text = text.lower().replace(' ', '').replace('|', 'i').replace('s', '5')
        
        # Look for the "x" + quantity pattern
        if 'x' in clean_text or (clean_text.isdigit() and len(clean_text) < 4):
            try:
                # Extract only numbers
                quantity = int(''.join(filter(str.isdigit, clean_text)))
                
                # Check next 3 lines for the name (Game fonts often split names)
                for j in range(1, 4):
                    if i + j < len(results):
                        potential_name = results[i+j][1].lower().replace('\n', ' ')
                        for herb in herb_list:
                            # Use partial matching in case OCR misses a letter
                            if herb.lower() in potential_name or potential_name in herb.lower():
                                found_data[herb] = quantity
                                break
            except:
                continue
    return found_data

# -------------------------------
# 2. MASTER APP SCRIPT
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

# (Keep your existing CSS here...)
st.markdown("""<style>
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
    .app-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border-radius: 15px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px; color: white; }
    .pill-title { color: #58a6ff; font-size: 1.3rem; font-weight: bold; margin: 0; }
    .qi-tag { background: rgba(63, 185, 80, 0.2); color: #3fb950; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 4px; }
    .badge { display: inline-block; background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; margin-top: 5px; border: 1px solid rgba(88, 166, 255, 0.2); }
    .total-box { margin-top: 12px; padding: 10px; background: rgba(0, 0, 0, 0.3); border-radius: 10px; border: 1px dashed rgba(88, 166, 255, 0.2); }
</style>""", unsafe_allow_html=True)

# Database
def get_db():
    return {
        "Nine Yang Pill": [{"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92}, {"tier": "Heavenly", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "black iron root": 2, "crimson flame mushroom": 1}, "qi": 120}],
        "Jade Tide Pill": [{"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150}, {"tier": "Heavenly", "ingredients": {"blue wave coral herb": 2, "black iron root": 1, "crimson flame mushroom": 1, "bitter jade grass": 2}, "qi": 162}],
        "Starborn Agility Pill": [{"tier": "Heavenly", "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230}],
        "Lotus Nirvana Pill": [{"tier": "Standard", "ingredients": {"thousand year lotus": 6}, "qi": 50}],
        "Dragon Pulse Pill": [{"tier": "Heavenly (V2)", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168}]
    }

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

for h in all_herbs:
    if f"i_{h}" not in st.session_state: st.session_state[f"i_{h}"] = 0

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

with tab2:
    st.markdown("### 📸 Image Decompiler")
    ss_file = st.file_uploader("Upload Inventory SS", type=['png', 'jpg', 'jpeg'])
    
    if ss_file:
        if st.button("✨ Scan Screenshot"):
            with st.spinner("Decoding materials..."):
                found = decompile_screenshot(ss_file, all_herbs)
                if found:
                    for herb, qty in found.items():
                        st.session_state[f"i_{herb}"] = qty
                    st.success(f"Detected {len(found)} items!")
                    st.rerun()
                else:
                    st.error("Reader failed. Ensure the screenshot is high quality and zoomed in.")

    st.divider()
    herb_search = st.text_input("🔍 Manual Edit...", "").lower()
    cols = st.columns(2)
    filtered = [h for h in all_herbs if herb_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 2]:
            st.number_input(h.title(), min_value=0, key=f"i_{h}")

with tab1:
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    craftable = []
    for name, variants in db.items():
        for v in variants:
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            if amt > 0:
                craftable.append({"name": name, "tier": v["tier"], "amt": amt, "qi": v["qi"], "ing": v["ingredients"]})

    if craftable:
        for p in sorted(craftable, key=lambda x: x['qi'], reverse=True):
            badges = "".join([f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in p["ing"].items()])
            totals = "".join([f'<div style="font-size: 0.8rem;">• {ing.title()}: <b>{req*p["amt"]}</b></div>' for ing, req in p["ing"].items()])
            st.markdown(f"""<div class="app-card">
                <div style="display:flex; justify-content:space-between;">
                    <div><div class="pill-tier">{p['tier']}</div><div class="pill-title">{p['name']}</div><span class="qi-tag">+{p['qi']}% Qi</span></div>
                    <div style="text-align:right;"><div style="font-size:0.6rem; color:#8b949e;">QTY</div><div style="font-size:1.8rem; color:#58a6ff; font-weight:bold;">{p['amt']}</div></div>
                </div>
                <div style="margin-top:10px;">{badges}</div>
                <div class="total-box"><b>BATCH ({p['amt']}x):</b><br>{totals}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("Cauldron empty. Scan a screenshot or add herbs manually.")
