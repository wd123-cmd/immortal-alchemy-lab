import streamlit as st
import cv2
import numpy as np
import easyocr
import re

# -------------------------------
# 1. THE DECOMPILER ENGINE
# -------------------------------
def decompile_screenshot(image_bytes):
    # Initialize the Reader (English)
    reader = easyocr.Reader(['en'])
    
    # Convert uploaded bytes to OpenCV format
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Perform OCR
    results = reader.readtext(img)
    
    found_inventory = {}
    
    # Logic: Look for "x" + Number, then look at the text immediately below it
    for i, (bbox, text, prob) in enumerate(results):
        clean_text = text.lower().strip()
        
        # Look for the quantity (e.g., "x12" or "12")
        if 'x' in clean_text or clean_text.isdigit():
            num_match = re.search(r'(\d+)', clean_text)
            if num_match:
                quantity = int(num_match.group(1))
                
                # Check the next few lines of text to find the Herb Name
                # Game screenshots usually place the name right under the number
                for j in range(1, 4):
                    if i + j < len(results):
                        potential_name = results[i+j][1].lower().strip()
                        
                        # Match against our master herb list
                        for herb in all_herbs:
                            if herb in potential_name:
                                found_inventory[herb] = quantity
                                break
    return found_inventory

# -------------------------------
# 2. UPDATED APP CODE
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

# ... [Insert your CSS from previous messages here] ...

# Load Database
def get_db():
    return {
        "Nine Yang Pill": [{"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92}],
        "Jade Tide Pill": [{"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150}],
        # ... [Rest of your pill database]
    }

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

# Persistent State
for h in all_herbs:
    if f"i_{h}" not in st.session_state: st.session_state[f"i_{h}"] = 0

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

with tab2:
    st.markdown("### 📸 Image Decompiler")
    uploaded_file = st.file_uploader("Paste or Upload Inventory SS", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        if st.button("✨ Decompile Screenshot"):
            with st.spinner("Decoding Alchemy Materials..."):
                results = decompile_screenshot(uploaded_file.read())
                
                if results:
                    for herb, qty in results.items():
                        st.session_state[f"i_{herb}"] = qty
                    st.success(f"Decompiled {len(results)} items successfully!")
                    st.rerun()
                else:
                    st.error("Could not find matching herbs. Try a clearer screenshot.")

    st.divider()
    st.markdown("### Manual Inventory")
    # ... [Your manual number_input grid code here]
