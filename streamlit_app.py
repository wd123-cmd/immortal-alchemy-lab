import streamlit as st
import cv2
import numpy as np
import easyocr
from PIL import Image, ImageEnhance
import difflib
import re

# ── OCR ENGINE ─────────────────────────────────────────────────────────────────

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)


# ── HERB ALIAS TABLE ───────────────────────────────────────────────────────────

_HERB_ALIAS_MAP = {
    "healing sunflower":     ["healing", "sunflower", "sundlng", "hcalig", "healig", "sunllower",
                               "sunllowe", "hcaling", "suadlag", "hlcaling", "hedig", "heali4g",
                               "heallig", "ealv"],
    "black iron root":       ["black", "ironroot", "ionadoot", "bladz", "bonroor", "bouroot",
                               "bladk", "kourooc", "bledk", "koro", "koroo", "bled", "korooz",
                               "ko", "rooz"],
    "blue wave coral herb":  ["blue", "wave", "coral", "ballaz", "coaileb", "ualheb", "oalhub",
                               "blugwav", "blugwavg", "uallub", "qbal", "ualleb", "dallazz"],
    "thousand year lotus":   ["thousand", "lotus", "hatsud", "yealoug", "yeaclos", "ibousand",
                               "tbousand", "uouard", "iboutnd", "ycclas", "yac", "ibosseadd", "yatoud"],
    "moonlight jade leaf":   ["moonlight", "jadeleaf", "saglui", "mopnlight", "meccligbt",
                               "jadalzar", "jadeleal", "jadelea", "mooclight", "meonligbt",
                               "jadglca", "saal", "meuuligbt", "saglti"],
    "ironbone grass":        ["ironbone", "gtass", "iobge", "kuboue", "ouboue", "bonbone",
                               "konbong", "iabssa", "gcass", "iabge"],
    "nine suns flame grass": ["ninesuns", "flamegrass"],
    "purple lightning orchid":["purple", "orchid", "lightning", "bistadattg", "ruplg",
                               "lipnnidg", "eunte"],
    "red ginseng":           ["ginseng", "red"],
    "bitter jade grass":     ["bitter", "jadegrass"],
    "cloud mist herb":       ["cloud", "mist", "mistherb", "candmse", "hedb", "dudsb", "hub"],
    "spirit spring herb":    ["spiritspring", "springherb"],
    "dandelion of qi":       ["dandelion", "ofqi"],
    "seven star flower":     ["sevenstar", "starflower", "setcnsaac", "flower", "sevez", "sur",
                               "8lst", "fte"],
    "starlight dew herb":    ["starlight", "dewherb"],
    "heavenly spirit vine":  ["heavenly", "spiritvine"],
    "mountain green herb":   ["mountain", "greenherb"],
    "wild spirit grass":     ["wildspirit", "wild", "budspide", "gas3", "wnika", "spinft", "eapnn"],
    "azure serpent grass":   ["azure", "serpent"],
    "wild bitter grass":     ["wildbitter", "bittergrass"],
}


def get_herb_aliases(herb_name: str) -> list[str]:
    """Return all known OCR variants / aliases for an herb name."""
    aliases = list(_HERB_ALIAS_MAP.get(herb_name.lower(), []))
    for word in herb_name.lower().split():
        if len(word) > 3:
            aliases.append(word)
    return list(set(aliases))


# ── OCR / IMAGE PROCESSING ─────────────────────────────────────────────────────

def _preprocess_image(img_cv: np.ndarray) -> np.ndarray:
    """Resize to a fixed 800 px width then enhance contrast with CLAHE."""
    h, w = img_cv.shape[:2]
    scale = 800 / w
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
    img_cv = cv2.resize(img_cv, None, fx=scale, fy=scale, interpolation=interp)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def _normalise_qty_token(token: str) -> str:
    """Fix common OCR misreads in quantity tokens (e.g. 'xlz' → 'x12')."""
    # Multi-char double-digit interceptor
    for bad in ("xz", "xlz", "xiz", "x2z", "xi2", "x|2", "xl2", "x22"):
        token = token.replace(bad, "x12")
    # Single-char misread as duplicate digit
    dupes = {"22": "x2", "44": "x4", "55": "x5"}
    if token in dupes:
        token = dupes[token]
    # Common single-glyph substitutions
    token = token.replace("i", "1").replace("|", "1").replace("l", "1")
    token = token.replace("s", "5").replace("o", "0").replace("z", "2")
    return token


def decompile_screenshot(image_file, herb_list: list) -> tuple[dict, list]:
    """OCR an inventory screenshot and return {herb: qty} plus raw debug text."""
    reader = load_ocr()
    try:
        image = Image.open(image_file).convert("RGB")
    except Exception:
        return {}, []

    img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    gray = _preprocess_image(img_cv)
    curr_h, curr_w = gray.shape[:2]

    results = reader.readtext(gray, text_threshold=0.2, low_text=0.2)

    numbers_found: list[dict] = []
    herbs_found:   list[dict] = []
    raw_text_seen: list[str]  = []

    for bbox, text, _prob in results:
        raw_text_seen.append(text)
        token = _normalise_qty_token(text.lower().replace(" ", ""))
        cx = (bbox[0][0] + bbox[1][0]) / 2
        cy = (bbox[0][1] + bbox[2][1]) / 2

        # ── Quantity token ──
        if ("x" in token or any(c.isdigit() for c in token)) and len(token) < 6:
            digits = "".join(filter(str.isdigit, token))
            if digits:
                numbers_found.append({"qty": int(digits), "x": cx, "y": cy})
            continue

        # ── Herb token ──
        word = re.sub(r"[^a-z]", "", text.lower())
        if len(word) < 3:
            continue
        matched_herb = None
        for herb in herb_list:
            aliases = get_herb_aliases(herb)
            if word in aliases:
                matched_herb = herb
                break
            for alias in aliases:
                if len(alias) > 3 and difflib.SequenceMatcher(None, word, alias).ratio() > 0.75:
                    matched_herb = herb
                    break
            if matched_herb:
                break
        if matched_herb:
            herbs_found.append({"herb": matched_herb, "x": cx, "y": cy})

    # ── Phase 2: geometry-based pairing ───────────────────────────────────────
    # Numbers that appear *above* a herb fragment and nearby on the x-axis
    # belong to that herb's quantity slot.
    max_y_dist = curr_h * 0.30
    max_x_dist = curr_w * 0.15
    found_data: dict[str, int] = {}

    for h_frag in herbs_found:
        best_num = None
        min_dist = float("inf")
        for num in numbers_found:
            y_diff = h_frag["y"] - num["y"]
            x_diff = abs(h_frag["x"] - num["x"])
            if 0 < y_diff < max_y_dist and x_diff < max_x_dist:
                dist = (x_diff ** 2 + y_diff ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    best_num = num
        if best_num:
            herb = h_frag["herb"]
            qty  = best_num["qty"]
            if herb not in found_data or qty > found_data[herb]:
                found_data[herb] = qty

    return found_data, raw_text_seen


# ── RECIPE DATABASE ────────────────────────────────────────────────────────────

def get_db() -> dict:
    return {
        "Nine Yang Pill": [
            {"tier": "Standard",  "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92},
            {"tier": "Heavenly",  "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "black iron root": 2, "crimson flame mushroom": 1}, "qi": 120},
        ],
        "Jade Tide Pill": [
            {"tier": "Standard",  "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150},
            {"tier": "Heavenly",  "ingredients": {"blue wave coral herb": 2, "black iron root": 1, "crimson flame mushroom": 1, "bitter jade grass": 2}, "qi": 162},
        ],
        "Stormheart Pill": [
            {"tier": "Heavenly",  "ingredients": {"cloud mist herb": 4, "spirit spring herb": 2}, "qi": 225},
        ],
        "Lotus Nirvana Pill": [
            {"tier": "Standard",  "ingredients": {"thousand year lotus": 6}, "qi": 50},
        ],
        "Starborn Agility Pill": [
            {"tier": "Imperfect", "ingredients": {"dandelion of qi": 1, "seven star flower": 2, "blue wave coral herb": 1, "cloud mist herb": 1, "spirit spring herb": 1}, "qi": 115},
            {"tier": "Heavenly",  "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230},
        ],
        "Dragon Pulse Pill": [
            {"tier": "Imperfect",     "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 80},
            {"tier": "Heavenly (V1)", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 160},
            {"tier": "Heavenly (V2)", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168},
        ],
        "Void Clarity Pill": [
            {"tier": "Standard",  "ingredients": {"starlight dew herb": 2, "cloud mist herb": 2, "heavenly spirit vine": 1, "bitter jade grass": 1}, "qi": 170},
        ],
        "Celestial Harmony Pill": [
            {"tier": "Imperfect", "ingredients": {"silverleaf herb": 1, "seven star flower": 1, "mountain green herb": 1, "qi dandelion": 1, "wild spirit grass": 2}, "qi": 90},
            {"tier": "Heavenly",  "ingredients": {"thousand year lotus": 1, "silverleaf herb": 1, "seven star flower": 3, "moonlight jade leaf": 1}, "qi": 236},
        ],
        "Seven Star Enlightenment": [
            {"tier": "Imperfect",       "ingredients": {"spirit spring herb": 1, "seven star flower": 2, "starlight dew herb": 2, "silverleaf herb": 1}, "qi": 125},
            {"tier": "Heavenly (Lotus)","ingredients": {"thousand year lotus": 2, "blue wave coral herb": 1, "heavenly spirit vine": 1, "starlight dew herb": 2}, "qi": 285},
            {"tier": "Heavenly (Pure)", "ingredients": {"heavenly spirit vine": 1, "starlight dew herb": 5}, "qi": 295},
        ],
        "Dragon Essence Pill": [
            {"tier": "Standard",  "ingredients": {"azure serpent grass": 1, "purple lightning orchid": 1, "nine suns flame grass": 1, "crimson flame mushroom": 2, "cloud mist herb": 1}, "qi": 0, "spec": "18% Lifespan"},
            {"tier": "Heavenly",  "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"},
        ],
        "Sun Roses Rebirth": [
            {"tier": "Vit V1", "ingredients": {"wild bitter grass": 2, "red ginseng": 1, "healing sunflower": 2, "mountain green herb": 1}, "qi": 0, "spec": "20% Vitality (Perm)"},
            {"tier": "Vit V2", "ingredients": {"mountain green herb": 3, "healing sunflower": 3}, "qi": 0, "spec": "20% Vitality (Perm)"},
            {"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"},
            {"tier": "Vit V4", "ingredients": {"healing sunflower": 2, "ironbone grass": 3, "red ginseng": 1}, "qi": 0, "spec": "41% Vitality (Perm)"},
        ],
        "Phoenix Ember Pill": [
            {"tier": "Standard", "ingredients": {"crimson flame mushroom": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 2, "spirit spring herb": 1}, "qi": 0, "spec": "70% Vit / 40% Spd"},
        ],
        "Mistveil Focus Pill": [
            {"tier": "Standard",  "ingredients": {"silverleaf herb": 3, "spirit spring herb": 3}, "qi": 238},
            {"tier": "Focus-V2",  "ingredients": {"silverleaf herb": 3, "spirit spring herb": 2, "seven star flower": 1}, "qi": 245},
            {"tier": "Focus-V3",  "ingredients": {"cloud mist herb": 2, "spirit spring herb": 2, "starlight dew herb": 1, "heavenly spirit vine": 1}, "qi": 260},
        ],
        "Concentration Pill": [
            {"tier": "Dandelion Mix", "ingredients": {"seven star flower": 1, "azure serpent grass": 3, "dandelion of qi": 2}, "qi": 100},
            {"tier": "Pure Mix",      "ingredients": {"seven star flower": 3, "azure serpent grass": 3}, "qi": 100},
            {"tier": "Spring Mix",    "ingredients": {"seven star flower": 1, "azure serpent grass": 3, "spirit spring herb": 2}, "qi": 100},
        ],
        "Ironclad Resolve": [
            {"tier": "Heavenly", "ingredients": {"silverleaf herb": 1, "moonlight jade leaf": 1, "spirit spring herb": 1, "crimson flame mushroom": 1, "black iron root": 2}, "qi": 0, "spec": "Perm Str/Vit"},
        ],
        "Tideborn Vigor": [
            {"tier": "Heavenly", "ingredients": {"wild spirit grass": 1, "wild bitter grass": 1, "red ginseng": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 1}, "qi": 0, "spec": "Vit/Str Boost"},
        ],
        "Blazewind Pill": [
            {"tier": "Heavenly", "ingredients": {"crimson flame mushroom": 2, "purple lightning orchid": 3, "wild spirit grass": 1}, "qi": 0, "spec": "Perm Spd/Str"},
        ],
        "Soul Replenishing": [
            {"tier": "Heavenly", "ingredients": {"healing sunflower": 2, "red ginseng": 1, "ironbone grass": 2, "seven star flower": 1}, "qi": 0, "spec": "12% Lifespan (Perm)"},
        ],
    }


# ── PAGE CONFIG & GLOBAL STYLES ────────────────────────────────────────────────

st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿",
                   initial_sidebar_state="collapsed")

st.markdown("""
<style>
  /* ── Base ─────────────────────────────────────────── */
  .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
  header { visibility: hidden; }
  footer { visibility: hidden; }

  /* ── Inputs: 16 px prevents iOS auto-zoom ─────────── */
  input, select, textarea { font-size: 16px !important; }
  div[data-baseweb="input"] {
    background-color: rgba(0,0,0,0.4) !important;
    border: 1px solid rgba(88,166,255,0.3) !important;
    border-radius: 8px !important;
  }

  /* ── Labels ───────────────────────────────────────── */
  label { color: #f0f6fc !important; font-weight: 600 !important; }

  /* ── Tabs ─────────────────────────────────────────── */
  .stTabs [data-baseweb="tab"] {
    background-color: rgba(255,255,255,0.05);
    color: #8b949e;
    border-radius: 8px 8px 0 0;
  }
  .stTabs [aria-selected="true"] {
    background-color: rgba(88,166,255,0.15) !important;
    color: #58a6ff !important;
    border-bottom: 2px solid #58a6ff !important;
  }

  /* ── Cards ────────────────────────────────────────── */
  .app-card {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(15px);
    border-radius: 15px;
    padding: 15px;
    border: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 15px;
    color: white;
  }
  .pill-title { color: #58a6ff; font-size: 1.2rem; font-weight: bold; margin: 0; }
  .badge {
    display: inline-block;
    background: rgba(88,166,255,0.1);
    color: #58a6ff;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.75rem;
    margin: 3px 3px 0 0;
    border: 1px solid rgba(88,166,255,0.2);
  }
  .total-box {
    margin-top: 12px;
    padding: 10px;
    background: rgba(0,0,0,0.3);
    border-radius: 10px;
    border: 1px dashed rgba(88,166,255,0.2);
  }
  .summary-box {
    background: rgba(88,166,255,0.07);
    border: 1px solid rgba(88,166,255,0.2);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 18px;
    color: white;
  }
  .app-header {
    text-align: center;
    padding: 12px 0 6px 0;
    margin-bottom: 10px;
  }
  /* clamp(min, preferred, max) — the preferred value is relative to font size
     so user zoom is respected while still scaling with viewport */
  .app-header h1 { color: #58a6ff; font-size: clamp(1.4rem, 2.5vw + 0.5rem, 2rem); margin: 0; }
  .app-header p  { color: #8b949e; font-size: 0.85rem; margin: 4px 0 0 0; }

  /* ── Mobile tweaks ────────────────────────────────── */
  @media (max-width: 768px) {
    .block-container { padding: 0.75rem 0.5rem !important; }
    .app-card { padding: 12px !important; }
    .pill-title { font-size: 1rem !important; }
    /* Touch-friendly inputs (44 px minimum tap target) */
    input, select, textarea { min-height: 44px !important; }
    /* Stack two-column grids on very narrow screens */
    [data-testid="column"] { min-width: 100% !important; }
  }
</style>
""", unsafe_allow_html=True)


# ── DATA & SESSION STATE ───────────────────────────────────────────────────────

db       = get_db()
all_herbs = sorted({h for v_list in db.values() for v in v_list for h in v["ingredients"]})

defaults: dict = {f"i_{h}": 0 for h in all_herbs}
defaults["debug_log"]   = []
defaults["handcrafted"] = False

for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── APP HEADER ─────────────────────────────────────────────────────────────────

st.markdown("""
<div class="app-header">
  <h1>🧿 Immortal Alchemy Lab</h1>
  <p>Scan your inventory · track your stock · craft the perfect pill</p>
</div>
""", unsafe_allow_html=True)


# ── GLOBAL CONTROLS (above tabs so both tabs share the same value) ─────────────

ctrl_l, ctrl_r = st.columns([3, 1])
with ctrl_l:
    p_query = st.text_input("🔍 Search recipes…", "", label_visibility="collapsed",
                             placeholder="🔍 Search recipes…").lower()
with ctrl_r:
    st.session_state["handcrafted"] = st.toggle(
        "✨ Handcrafted (3× Qi)", value=st.session_state["handcrafted"])

handcrafted: bool = st.session_state["handcrafted"]


# ── MAIN TABS ──────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(["🥣 Lab Dashboard", "🎒 Ingredients Chest"])

# ════════════════════════════════════════════════════════════════════════════════
with tab2:
# ════════════════════════════════════════════════════════════════════════════════
    st.markdown("### 📸 Visual Decompiler")
    ss_file = st.file_uploader("Upload Inventory Screenshot", type=["png", "jpg", "jpeg"])

    if ss_file:
        if st.button("✨ Decompile Image", use_container_width=True):
            with st.spinner("Scanning image & matching herbs…"):
                found, raw_text = decompile_screenshot(ss_file, all_herbs)
                st.session_state["debug_log"] = raw_text
                if found:
                    for herb, qty in found.items():
                        st.session_state[f"i_{herb}"] += qty
                    st.success(f"Added {len(found)} herb type(s) to your chest!")
                    st.rerun()
                else:
                    st.error("No herbs matched. Check the raw debug data below for clues.")

    if st.session_state["debug_log"]:
        with st.expander("🛠️ Raw OCR output (debug)"):
            st.caption("Exactly what the AI read from your last scan:")
            st.write(st.session_state["debug_log"])

    st.divider()

    btn_col, _ = st.columns([1, 2])
    with btn_col:
        if st.button("🧹 Clear All Stock", use_container_width=True):
            for h in all_herbs:
                st.session_state[f"i_{h}"] = 0
            st.session_state["debug_log"] = []
            st.rerun()

    h_search = st.text_input("🔍 Filter / edit herbs…", "",
                              placeholder="type an herb name…").lower()
    filtered = [h for h in all_herbs if h_search in h]

    cols = st.columns(2)
    for i, h in enumerate(filtered):
        with cols[i % 2]:
            st.number_input(h.title(), min_value=0, key=f"i_{h}", step=1)


# ════════════════════════════════════════════════════════════════════════════════
with tab1:
# ════════════════════════════════════════════════════════════════════════════════
    inv = {h: st.session_state[f"i_{h}"] for h in all_herbs}
    craftable: list[dict] = []

    for name, variants in db.items():
        for v in variants:
            possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
            amt = min(possible) if possible else 0
            if amt <= 0:
                continue
            qi_val = v["qi"] * 3 if handcrafted else v["qi"]
            spec   = v.get("spec")
            if p_query and not any(p_query in s.lower() for s in [name, v["tier"], spec or ""]):
                continue
            craftable.append({
                "name": name, "tier": v["tier"], "amt": amt,
                "qi": qi_val, "spec": spec, "ing": v["ingredients"],
            })

    if not craftable:
        st.info("No craftable items. Upload a screenshot or add ingredients manually in the Chest tab.")
    else:
        # ── Aggregate totals across every craftable recipe ─────────────────────
        totals_all: dict[str, int] = {}
        for p in craftable:
            for ing, req in p["ing"].items():
                totals_all[ing] = totals_all.get(ing, 0) + req * p["amt"]

        with st.expander(f"📦 Total ingredients needed ({len(craftable)} craftable recipes)", expanded=False):
            st.markdown('<div class="summary-box">', unsafe_allow_html=True)
            rows = sorted(totals_all.items(), key=lambda x: x[1], reverse=True)
            half = (len(rows) + 1) // 2
            sc1, sc2 = st.columns(2)
            for col, chunk in ((sc1, rows[:half]), (sc2, rows[half:])):
                with col:
                    for ing, need in chunk:
                        have = inv.get(ing, 0)
                        ok = have >= need
                        color  = "#3fb950" if ok else "#f85149"
                        icon   = "✓" if ok else "✗"
                        st.markdown(
                            f'<div style="font-size:0.82rem; margin-bottom:3px;">'
                            f'<span style="color:{color};font-weight:bold;">{icon}</span> '
                            f'{ing.title()}: <b style="color:{color}">{need}</b>'
                            f' <span style="color:#8b949e">(have {have})</span></div>',
                            unsafe_allow_html=True,
                        )
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Individual recipe cards ────────────────────────────────────────────
        for p in sorted(craftable, key=lambda x: x["qi"], reverse=True):
            is_perm = any(w in (p["spec"] or "").lower() for w in ("perm", "lifespan", "nirvana"))
            perm_tag = "Permanent" if is_perm else "Temporary"
            tags = (
                f'<span style="background:rgba(255,255,255,0.1);color:white;'
                f'padding:2px 7px;border-radius:4px;font-size:0.7rem;margin-right:4px;">'
                f'{perm_tag}</span>'
            )
            if p["qi"] > 0:
                tags += (
                    f'<span style="background:rgba(63,185,80,0.2);color:#3fb950;'
                    f'padding:2px 7px;border-radius:4px;font-size:0.7rem;margin-right:4px;">'
                    f'+{p["qi"]}% Qi</span>'
                )
            if p["spec"]:
                for s in p["spec"].split("/"):
                    tags += (
                        f'<span style="background:rgba(187,128,255,0.2);color:#d2a8ff;'
                        f'padding:2px 7px;border-radius:4px;font-size:0.7rem;margin-right:4px;">'
                        f'{s.strip()}</span>'
                    )

            badges = "".join(
                f'<span class="badge">{ing.title()}: {req}</span>'
                for ing, req in p["ing"].items()
            )
            batch_totals = "".join(
                f'<div style="font-size:0.82rem;margin-bottom:2px;">• {ing.title()}: <b>{req * p["amt"]}</b></div>'
                for ing, req in p["ing"].items()
            )

            st.markdown(f"""
<div class="app-card">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
    <div style="flex:1;min-width:0;">
      <div style="color:#8b949e;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em;">{p['tier']}</div>
      <div class="pill-title">{p['name']}</div>
      <div style="margin-top:5px;flex-wrap:wrap;">{tags}</div>
    </div>
    <div style="text-align:center;flex-shrink:0;">
      <div style="font-size:0.6rem;color:#8b949e;letter-spacing:.08em;">BATCH</div>
      <div style="font-size:2rem;color:#58a6ff;font-weight:bold;line-height:1;">{p['amt']}</div>
    </div>
  </div>
  <div style="margin-top:10px;line-height:1.8;">{badges}</div>
  <div class="total-box"><b style="font-size:0.8rem;">BATCH MATERIALS:</b><br>{batch_totals}</div>
</div>
""", unsafe_allow_html=True)
