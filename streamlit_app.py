import streamlit as st

# -------------------------------
# APP CONFIG & MOBILE-FORCED STYLING
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

st.markdown("""
    <style>
    /* Global Background */
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Force Centering and Mobile Spacing */
    .main-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }
    
    .centered-title {
        text-align: center;
        color: white;
        width: 100%;
        margin-top: 10px;
    }

    /* Visual Card Styling - NO INDENTATION in f-strings to prevent 'code block' look */
    .app-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        border-radius: 15px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
        color: white;
        width: 100%;
    }

    /* Tag and Badge styles */
    .pill-title { color: #58a6ff; font-size: 1.3rem; font-weight: bold; margin: 0; }
    .pill-tier { color: #8b949e; font-size: 0.7rem; text-transform: uppercase; margin-bottom: 4px; }
    
    .benefit-tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 4px;
        margin-top: 4px;
    }
    .qi-tag { background: rgba(63, 185, 80, 0.2); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.3); }
    .spec-tag { background: rgba(187, 128, 255, 0.2); color: #d2a8ff; border: 1px solid rgba(187, 128, 255, 0.3); }
    .dur-tag { background: rgba(255, 255, 255, 0.1); color: #f0f6fc; }
    
    .badge {
        display: inline-block;
        background: rgba(88, 166, 255, 0.1);
        color: #58a6ff;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.75rem;
        margin-right: 5px;
        margin-top: 5px;
        border: 1px solid rgba(88, 166, 255, 0.2);
    }
    
    .total-box {
        margin-top: 12px;
        padding: 10px;
        background: rgba(0, 0, 0, 0.3);
        border-radius: 10px;
        border: 1px dashed rgba(88, 166, 255, 0.2);
    }

    /* Fixed Metrics for Mobile */
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; text-align: center !important; }
    [data-testid="stMetricLabel"] { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# DATASET
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
# INVENTORY
# -------------------------------
db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

with st.sidebar:
    st.markdown("<h1 style='color:#58a6ff;'>📦 Storage</h1>", unsafe_allow_html=True)
    handcrafted = st.toggle("✨ Handcrafted (3x)")
    if st.button("🧹 Clear Inventory"):
        for h in all_herbs: st.session_state[f"i_{h}"] = 0
        st.rerun()
    herb_filter = st.text_input("🔍 Filter Herbs", "")
    inv = {h: st.number_input(h.title(), min_value=0, key=f"i_{h}") if herb_filter.lower() in h.lower() else st.session_state.get(f"i_{h}", 0) for h in all_herbs}

# -------------------------------
# DASHBOARD
# -------------------------------
st.markdown("<div class='centered-title'><h1>Alchemy Dashboard</h1></div>", unsafe_allow_html=True)
pill_query = st.text_input("🔍 Live Search Recipes...", placeholder="Pill name or effect...").lower()

# Calc logic
craftable = []
for name, variants in db.items():
    for v in variants:
        possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
        amt = min(possible) if possible else 0
        if amt > 0:
            qi_val = v["qi"] * 3 if handcrafted else v["qi"]
            if not pill_query or pill_query in name.lower() or pill_query in v.get('spec', '').lower() or pill_query in v['tier'].lower():
                craftable.append({"name": name, "tier": v["tier"], "amt": amt, "qi": qi_val, "spec": v.get("spec"), "ing": v["ingredients"]})

# Stockpile Metric Only
st.metric("Total Items in Stock", sum(inv.values()))

# Main Display Area
if craftable:
    for p in sorted(craftable, key=lambda x: x['qi'], reverse=True):
        is_perm = any(w in (p['spec'] or "").lower() for w in ["perm", "lifespan", "nirvana"])
        dur = "Permanent" if is_perm else "Temporary"
        
        tags = f'<span class="benefit-tag dur-tag">{dur}</span>'
        if p['qi'] > 0: tags += f'<span class="benefit-tag qi-tag">+{p["qi"]}% Qi</span>'
        if p['spec']:
            for s in p['spec'].split('/'): tags += f'<span class="benefit-tag spec-tag">{s.strip()}</span>'

        badges = "".join([f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in p["ing"].items()])
        totals = "".join([f'<div style="font-size: 0.8rem; margin-bottom: 2px;">• {ing.title()}: <b>{req*p["amt"]}</b></div>' for ing, req in p["ing"].items()])
        
        # HTML Cards - MINIMIZED indent to prevent Streamlit interpreting as code blocks
        card_html = f"""<div class="app-card">
<div style="display: flex; justify-content: space-between; align-items: center;">
<div><div class="pill-tier">{p['tier']}</div><div class="pill-title">{p['name']}</div>{tags}</div>
<div style="text-align: right;"><div style="font-size: 0.6rem; color: #8b949e;">QTY</div><div style="font-size: 2rem; color: #58a6ff; font-weight: bold;">{p['amt']}</div></div>
</div>
<div style="margin-top:10px;">{badges}</div>
<div class="total-box">
<div style="font-size: 0.75rem; color:#58a6ff; font-weight:bold; margin-bottom:4px;">BATCH ({p['amt']}x)</div>
{totals}
</div>
</div>"""
        st.markdown(card_html, unsafe_allow_html=True)
else:
    st.markdown("<div class='floating-cauldron'>🥣</div>", unsafe_allow_html=True)
