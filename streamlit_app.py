import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image, UnidentifiedImageError
import difflib
import re
from typing import Dict, Iterable, List, Optional, Tuple

OCR_TARGET_WIDTH = 800
MAX_Y_DIST_FACTOR = 0.3
MAX_X_DIST_FACTOR = 0.15
FUZZY_MATCH_THRESHOLD = 0.75

HERB_ALIAS_SEEDS: Dict[str, List[str]] = {
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
    "wild bitter grass": ["wildbitter", "bittergrass"],
}

# -------------------------------
# 1. DYNAMIC RAYCASTER ENGINE (Fast & Accurate)
# -------------------------------
@st.cache_resource
def load_ocr() -> easyocr.Reader:
    return easyocr.Reader(["en"], gpu=False)


@st.cache_data(show_spinner=False)
def build_alias_map(herb_list: Tuple[str, ...]) -> Dict[str, Tuple[str, ...]]:
    alias_map: Dict[str, Tuple[str, ...]] = {}
    for herb in herb_list:
        base_aliases = set(HERB_ALIAS_SEEDS.get(herb.lower(), []))
        base_aliases.update({word for word in herb.lower().split() if len(word) > 3})
        alias_map[herb] = tuple(sorted(base_aliases))
    return alias_map


def normalize_number_text(text: str) -> str:
    clean = text.lower().replace(" ", "")
    replacements = [
        ("xz", "x12"),
        ("xlz", "x12"),
        ("xiz", "x12"),
        ("x2z", "x12"),
        ("xi2", "x12"),
        ("x|2", "x12"),
        ("xl2", "x12"),
        ("x22", "x12"),
    ]
    for old, new in replacements:
        clean = clean.replace(old, new)

    if clean == "22":
        clean = "x2"
    if clean == "44":
        clean = "x4"
    if clean == "55":
        clean = "x5"

    clean = clean.replace("i", "1").replace("|", "1").replace("l", "1")
    clean = clean.replace("s", "5").replace("o", "0").replace("z", "2")
    return clean


def extract_quantity(clean_text: str) -> Optional[int]:
    if ("x" in clean_text or any(char.isdigit() for char in clean_text)) and len(clean_text) < 6:
        digits = "".join(filter(str.isdigit, clean_text))
        if digits:
            return int(digits)
    return None


def match_herb(word: str, alias_map: Dict[str, Tuple[str, ...]]) -> Optional[str]:
    for herb, aliases in alias_map.items():
        if word in aliases:
            return herb
        for alias in aliases:
            if len(alias) > 3 and difflib.SequenceMatcher(None, word, alias).ratio() > FUZZY_MATCH_THRESHOLD:
                return herb
    return None

def decompile_screenshot(image_file, alias_map: Dict[str, Tuple[str, ...]]):
    reader = load_ocr()
    try:
        image = Image.open(image_file)
    except UnidentifiedImageError:
        return {}, ["Invalid image file."], "Invalid image file."

    img_array = np.array(image)
    if img_array.size == 0:
        return {}, ["Empty image data."], "Empty image data."

    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    _, width = img_cv.shape[:2]
    if width <= 0:
        return {}, ["Invalid image width."], "Invalid image width."

    scale = OCR_TARGET_WIDTH / width
    img_cv = cv2.resize(
        img_cv,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
    )

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray, text_threshold=0.2, low_text=0.2)

    curr_h, curr_w = gray.shape[:2]
    numbers_found = []
    herbs_found = []
    raw_text_seen = []

    for bbox, text, _ in results:
        raw_text_seen.append(text)
        clean = normalize_number_text(text)
        cx = (bbox[0][0] + bbox[1][0]) / 2
        cy = (bbox[0][1] + bbox[2][1]) / 2

        qty = extract_quantity(clean)
        if qty is not None:
            numbers_found.append({"qty": qty, "x": cx, "y": cy})
            continue

        word = re.sub(r"[^a-z]", "", text.lower())
        if len(word) < 3:
            continue

        matched_herb = match_herb(word, alias_map)
        if matched_herb:
            herbs_found.append({"herb": matched_herb, "x": cx, "y": cy})

    found_data: Dict[str, int] = {}
    max_y_dist = curr_h * MAX_Y_DIST_FACTOR
    max_x_dist = curr_w * MAX_X_DIST_FACTOR

    for h_frag in herbs_found:
        best_num = None
        min_dist = float("inf")

        for num in numbers_found:
            y_diff = h_frag["y"] - num["y"]
            x_diff = abs(h_frag["x"] - num["x"])

            if 0 < y_diff < max_y_dist and x_diff < max_x_dist:
                dist = (x_diff**2 + y_diff**2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    best_num = num

        if best_num:
            herb = h_frag["herb"]
            qty = best_num["qty"]
            if herb not in found_data or qty > found_data[herb]:
                found_data[herb] = qty

    return found_data, raw_text_seen, None

# -------------------------------
# 2. FULL RECIPE DATABASE
# -------------------------------
@st.cache_data(show_spinner=False)
def get_db() -> Dict[str, List[Dict[str, object]]]:
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


def build_pill_tags(pill: Dict[str, object]) -> str:
    tags: List[str] = []
    spec = (pill.get("spec") or "").lower()
    is_perm = any(word in spec for word in ["perm", "lifespan", "nirvana"])
    tags.append(
        f'<span style="background:rgba(255,255,255,0.1); color:white; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-right:4px;">'
        f'{"Permanent" if is_perm else "Temporary"}</span>'
    )
    qi_value = int(pill.get("qi") or 0)
    if qi_value > 0:
        tags.append(
            f'<span style="background:rgba(63,185,80,0.2); color:#3fb950; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-right:4px;">'
            f'+{qi_value}% Qi</span>'
        )
    if pill.get("spec"):
        for item in str(pill["spec"]).split("/"):
            tags.append(
                f'<span style="background:rgba(187,128,255,0.2); color:#d2a8ff; padding:2px 6px; border-radius:4px; font-size:0.7rem; margin-right:4px;">'
                f'{item.strip()}</span>'
            )
    return "".join(tags)


def build_badges(ingredients: Dict[str, int]) -> str:
    return "".join(
        f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in ingredients.items()
    )


def build_totals(ingredients: Dict[str, int], multiplier: int) -> str:
    return "".join(
        f'<div style="font-size: 0.8rem; margin-bottom:2px;">• {ing.title()}: <b>{req * multiplier}</b></div>'
        for ing, req in ingredients.items()
    )


def render_recipe_card(pill: Dict[str, object]) -> None:
    tags = build_pill_tags(pill)
    badges = build_badges(pill["ing"])
    totals = build_totals(pill["ing"], pill["amt"])
    st.markdown(
        f"""<div class="app-card">
                <div style="display:flex; justify-content:space-between; gap:12px;">
                    <div><div style="color:#8b949e; font-size:0.7rem;">{pill['tier']}</div><div class="pill-title">{pill['name']}</div><div style="margin-top:4px;">{tags}</div></div>
                    <div style="text-align:right;"><div style="font-size:0.6rem; color:#8b949e;">BATCH</div><div style="font-size:1.8rem; color:#58a6ff; font-weight:bold;">{pill['amt']}</div></div>
                </div>
                <div style="margin-top:10px;">{badges}</div>
                <div class="total-box"><b>BATCH MATERIALS:</b><br>{totals}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def init_session_state(herbs: Iterable[str]) -> None:
    for herb in herbs:
        st.session_state.setdefault(f"i_{herb}", 0)
    st.session_state.setdefault("debug_log", [])
    st.session_state.setdefault("handcrafted", False)

# -------------------------------
# 3. APP STYLING & INIT
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

st.markdown(
    """<style>
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

    @media (max-width: 900px) {
        .pill-title { font-size: 1.1rem; }
        .badge { font-size: 0.7rem; padding: 4px 8px; }
        .stTabs [data-baseweb="tab"] { font-size: 0.85rem; padding: 6px 10px; }
        div[data-testid="stHorizontalBlock"] { flex-direction: column; gap: 0.6rem; }
        div[data-testid="stHorizontalBlock"] > div { width: 100% !important; }
        .stButton > button, .stDownloadButton > button { width: 100%; }
    }
    </style>""",
    unsafe_allow_html=True,
)

db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))
alias_map = build_alias_map(tuple(all_herbs))
init_session_state(all_herbs)

# -------------------------------
# 4. MAIN INTERFACE TABS
# -------------------------------
tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

with tab2:
    st.markdown("### 📸 Visual Decompiler")
    st.caption("Tip: crop tightly around the inventory list for the fastest and most accurate scan.")
    ss_file = st.file_uploader(
        "Upload Inventory Screenshot",
        type=["png", "jpg", "jpeg"],
        key="inventory_upload",
    )
    
    if ss_file:
        if st.button("✨ Decompile Image", use_container_width=True):
            with st.spinner("Raycasting Layout & Decoding Herbs..."):
                found, raw_text, error = decompile_screenshot(ss_file, alias_map)

                st.session_state["debug_log"] = raw_text

                if error:
                    st.error(error)
                elif found:
                    for herb, qty in found.items():
                        st.session_state[f"i_{herb}"] += qty

                    st.success(f"Successfully added {len(found)} herbs to your chest!")
                    st.rerun()
                else:
                    st.error("Reader failed to match herbs. Check Debug data below.")

    if st.session_state["debug_log"]:
        with st.expander("🛠️ View Raw AI Data (Debug)"):
            st.write("This is exactly what the AI saw in the last scan:")
            st.write(st.session_state["debug_log"])

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🧹 Clear All Stock", use_container_width=True):
            for h in all_herbs: 
                st.session_state[f"i_{h}"] = 0
            st.session_state["debug_log"] = []
            st.rerun()
    with c2:
        st.toggle("✨ Handcrafted (3x)", key="handcrafted")
    
    h_search = st.text_input("🔍 Manual Search/Edit...", key="herb_search").lower().strip()
    cols = st.columns(2)
    filtered = [h for h in all_herbs if h_search in h]
    for i, h in enumerate(filtered):
        with cols[i % 2]: 
            st.number_input(h.title(), min_value=0, key=f"i_{h}")

with tab1:
    p_query = st.text_input("🔍 Live Search Recipes...", key="pill_search").lower().strip()
    handcrafted = st.session_state["handcrafted"]
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    craftable = []
    
    for name, variants in db.items():
        for v in variants:
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            if amt > 0:
                qi_val = v["qi"] * 3 if handcrafted else v["qi"]
                search_blob = f"{name.lower()} {v.get('spec', '').lower()} {v['tier'].lower()}"
                if not p_query or p_query in search_blob:
                    craftable.append(
                        {
                            "name": name,
                            "tier": v["tier"],
                            "amt": amt,
                            "qi": qi_val,
                            "spec": v.get("spec"),
                            "ing": v["ingredients"],
                        }
                    )

    if craftable:
        for pill in sorted(craftable, key=lambda item: item["qi"], reverse=True):
            render_recipe_card(pill)
    else: 
        st.info("No craftable items. Scan a screenshot or add ingredients manually.")
