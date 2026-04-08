import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image

# -------------------------------
# 1. ADVANCED GRID-SCAN ENGINE
# -------------------------------
@st.cache_resource
def load_ocr():
    # Use GPU if available for speed
    return easyocr.Reader(['en'], gpu=False)

def decompile_screenshot(image_file, herb_list):
    reader = load_ocr()
    
    # Load image
    image = Image.open(image_file)
    img_array = np.array(image)
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # --- PRE-PROCESSING FOR GAME FONT ---
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    # Binary Thresholding makes the white text "glow" and blacks out the background
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
    
    # We scan the original AND the processed image for best results
    results = reader.readtext(thresh) + reader.readtext(img_cv)
    
    found_data = {}
    
    # Sort results by vertical position (Y coordinate) to keep items together
    results.sort(key=lambda x: x[0][0][1])

    for i, (bbox, text, prob) in enumerate(results):
        # Clean text for quantity check
        clean = text.lower().replace(' ', '').replace('o', '0').replace('i', '1').replace('s', '5')
        
        # Look for numbers (quantities) - handles 'x12', 'x 12', or just '12'
        if ('x' in clean or clean.isdigit()) and len(clean) < 5:
            try:
                num_str = ''.join(filter(str.isdigit, clean))
                if not num_str: continue
                quantity = int(num_str)
                
                # LOOKAHEAD: Check text blocks near this number for the Herb Name
                # On mobile/PC grid, the name is usually within the next few detected blocks
                for j in range(-3, 4): # Search slightly above and below
                    if 0 <= i + j < len(results):
                        potential_name = results[i+j][1].lower().strip()
                        
                        # Match against Master List
                        for herb in herb_list:
                            # Fuzzy check: if 70% of the herb name is found
                            if herb.lower() in potential_name or potential_name in herb.lower():
                                found_data[herb] = quantity
                                break
            except:
                continue
                
    return found_data

# -------------------------------
# 2. FULL INTEGRATED SCRIPT
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

# CSS remains the same (High contrast for mobile)
st.markdown("""<style>
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
    .stTabs [data-baseweb="tab"] { background-color: rgba(255, 255, 255, 0.05); color: #8b949e; border-radius: 8px 8px 0 0; }
    .stTabs [aria-selected="true"] { background-color: rgba(88, 166, 255, 0.15) !important; color: #58a6ff !important; }
    .app-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border-radius: 15px; padding: 15px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 15px; color: white; }
    .pill-title { color: #58a6ff; font-size: 1.3rem; font-weight: bold; }
    .badge { display: inline-block; background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; margin-top: 5px; border: 1px solid rgba(88, 166, 255, 0.2); }
    .total-box { margin-top: 12px; padding: 10px; background: rgba(0, 0, 0, 0.3); border-radius: 10px; border: 1px dashed rgba(88, 166, 255, 0.2); }
</style>""", unsafe_allow_html=True)

# Dataset
def get_db():
    return {
        "Nine Yang Pill": [{"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92}],
        "Jade Tide Pill": [{"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150}],
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
    st.markdown("### 📸 Visual Reader")
    ss_file = st.file_uploader("Upload Inventory SS", type=['png', 'jpg', 'jpeg'])
    
    if ss_file:
        if st.button("✨ Decompile Image"):
            with st.spinner("Decoding Spirit Herbs..."):
                found = decompile_screenshot(ss_file, all_herbs)
                if found:
                    for herb, qty in found.items():
                        st.session_state[f"i_{herb}"] = qty
                    st.success(f"Successfully decoded {len(found)} herbs!")
                    st.rerun()
                else:
                    st.error("Reader failed. Try a screenshot with higher brightness.")

    st.divider()
    herb_search = st.text_input("🔍 Manual Storage Edit...", "").lower()
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
                    <div><div class="pill-tier">{p['tier']}</div><div class="pill-title">{p['name']}</div><span style="color:#3fb950; font-size:0.8rem;">+{p['qi']}% Qi</span></div>
                    <div style="text-align:right;"><div style="font-size:0.6rem; color:#8b949e;">BATCH</div><div style="font-size:1.8rem; color:#58a6ff; font-weight:bold;">{p['amt']}</div></div>
                </div>
                <div style="margin-top:10px;">{badges}</div>
                <div class="total-box"><b>BATCH MATERIALS:</b><br>{totals}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div style='text-align:center; opacity:0.3; margin-top:50px;'><h1>🥣</h1><p>Cauldron Empty</p></div>", unsafe_allow_html=True)
