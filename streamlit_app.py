import streamlit as st

# -------------------------------
# APP CONFIG & NATIVE APP STYLING
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

# CSS Injection
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }
    .floating-cauldron { animation: float 3s ease-in-out infinite; font-size: 5rem; text-align: center; }

    .app-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        border-radius: 20px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 25px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        color: white;
    }
    
    .pill-title { color: #58a6ff; font-size: 1.6rem; font-weight: 700; margin: 0; }
    .pill-tier { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px; }
    
    .benefit-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-right: 8px;
        margin-top: 5px;
    }
    .qi-tag { background: rgba(63, 185, 80, 0.15); color: #3fb950; border: 1px solid rgba(63, 185, 80, 0.3); }
    .spec-tag { background: rgba(187, 128, 255, 0.15); color: #d2a8ff; border: 1px solid rgba(187, 128, 255, 0.3); }
    
    .badge {
        display: inline-block;
        background: rgba(88, 166, 255, 0.1);
        color: #58a6ff;
        padding: 6px 14px;
        border-radius: 8px;
        font-size: 0.85rem;
        margin-right: 10px;
        margin-top: 10px;
        border: 1px solid rgba(88, 166, 255, 0.2);
    }
    
    .total-box {
        margin-top: 20px;
        padding: 15px;
        background: rgba(0, 0, 0, 0.25);
        border-radius: 15px;
        border: 1px dashed rgba(88, 166, 255, 0.3);
    }

    .discovery-card {
        background: rgba(255, 171, 112, 0.05);
        border: 1px solid rgba(255, 171, 112, 0.2);
        padding: 15px;
        border-radius: 15px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# DATASET
# -------------------------------
def get_db():
    return {
        "Nine Yang Pill": [
            {"tier": "Standard", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "ironbone grass": 2, "crimson flame mushroom": 1}, "qi": 92},
            {"tier": "Heavenly", "ingredients": {"nine suns flame grass": 2, "purple lightning orchid": 1, "black iron root": 2, "crimson flame mushroom": 1}, "qi": 120}
        ],
        "Jade Tide Pill": [
            {"tier": "Standard", "ingredients": {"blue wave coral herb": 2, "moonlight jade leaf": 2, "red ginseng": 1, "bitter jade grass": 1}, "qi": 150},
            {"tier": "Heavenly", "ingredients": {"blue wave coral herb": 2, "black iron root": 1, "crimson flame mushroom": 1, "bitter jade grass": 2}, "qi": 162}
        ],
        "Stormheart Pill": [
            {"tier": "Heavenly", "ingredients": {"cloud mist herb": 4, "spirit spring herb": 2}, "qi": 225}
        ],
        "Lotus Nirvana Pill": [
            {"tier": "Standard", "ingredients": {"thousand year lotus": 6}, "qi": 50}
        ],
        "Starborn Agility Pill": [
            {"tier": "Imperfect", "ingredients": {"dandelion of qi": 1, "seven star flower": 2, "blue wave coral herb": 1, "cloud mist herb": 1, "spirit spring herb": 1}, "qi": 115},
            {"tier": "Heavenly", "ingredients": {"seven star flower": 5, "cloud mist herb": 1}, "qi": 230}
        ],
        "Dragon Pulse Pill": [
            {"tier": "Imperfect", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 80},
            {"tier": "Heavenly (V1)", "ingredients": {"blue wave coral herb": 2, "cloud mist herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 160},
            {"tier": "Heavenly (V2)", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168}
        ],
        "Void Clarity Pill": [
            {"tier": "Standard", "ingredients": {"starlight dew herb": 2, "cloud mist herb": 2, "heavenly spirit vine": 1, "bitter jade grass": 1}, "qi": 170}
        ],
        "Celestial Harmony Pill": [
            {"tier": "Imperfect", "ingredients": {"silverleaf herb": 1, "seven star flower": 1, "mountain green herb": 1, "qi dandelion": 1, "wild spirit grass": 2}, "qi": 90},
            {"tier": "Heavenly", "ingredients": {"thousand year lotus": 1, "silverleaf herb": 1, "seven star flower": 3, "moonlight jade leaf": 1}, "qi": 236}
        ],
        "Seven Star Enlightenment": [
            {"tier": "Imperfect", "ingredients": {"spirit spring herb": 1, "seven star flower": 2, "starlight dew herb": 2, "silverleaf herb": 1}, "qi": 125},
            {"tier": "Heavenly (Lotus)", "ingredients": {"thousand year lotus": 2, "blue wave coral herb": 1, "heavenly spirit vine": 1, "starlight dew herb": 2}, "qi": 285},
            {"tier": "Heavenly (Pure)", "ingredients": {"heavenly spirit vine": 1, "starlight dew herb": 5}, "qi": 295}
        ],
        "Dragon Essence Pill": [
            {"tier": "Standard", "ingredients": {"azure serpent grass": 1, "purple lightning orchid": 1, "nine suns flame grass": 1, "crimson flame mushroom": 2, "cloud mist herb": 1}, "qi": 0, "spec": "18% Lifespan"},
            {"tier": "Heavenly", "ingredients": {"heavenly spirit vine": 2, "purple lightning orchid": 1, "nine suns flame grass": 1, "moonlight jade leaf": 1}, "qi": 0, "spec": "24% Lifespan"}
        ],
        "Sun Roses Rebirth": [
            {"tier": "Vit V1", "ingredients": {"wild bitter grass": 2, "red ginseng": 1, "healing sunflower": 2, "mountain green herb": 1}, "qi": 0, "spec": "20% Vitality (Perm)"},
            {"tier": "Vit V2", "ingredients": {"mountain green herb": 3, "healing sunflower": 3}, "qi": 0, "spec": "20% Vitality (Perm)"},
            {"tier": "Vit V3", "ingredients": {"healing sunflower": 2, "ironbone grass": 2, "red ginseng": 1, "crimson flame mushroom": 1}, "qi": 0, "spec": "45% Vitality (Perm)"},
            {"tier": "Vit V4", "ingredients": {"healing sunflower": 2, "ironbone grass": 3, "red ginseng": 1}, "qi": 0, "spec": "41% Vitality (Perm)"}
        ],
        "Phoenix Ember Pill": [
            {"tier": "Standard", "ingredients": {"crimson flame mushroom": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 2, "spirit spring herb": 1}, "qi": 0, "spec": "70% Vit / 40% Spd"}
        ],
        "Mistveil Focus Pill": [
            {"tier": "Standard", "ingredients": {"silverleaf herb": 3, "spirit spring herb": 3}, "qi": 238},
            {"tier": "Focus-V2", "ingredients": {"silverleaf herb": 3, "spirit spring herb": 2, "seven star flower": 1}, "qi": 245},
            {"tier": "Focus-V3", "ingredients": {"cloud mist herb": 2, "spirit spring herb": 2, "starlight dew herb": 1, "heavenly spirit vine": 1}, "qi": 260}
        ],
        "Concentration Pill": [
            {"tier": "Dandelion Mix", "ingredients": {"seven star flower": 1, "azure serpent grass": 3, "dandelion of qi": 2}, "qi": 100},
            {"tier": "Pure Mix", "ingredients": {"seven star flower": 3, "azure serpent grass": 3}, "qi": 100},
            {"tier": "Spring Mix", "ingredients": {"seven star flower": 1, "azure serpent grass": 3, "spirit spring herb": 2}, "qi": 100}
        ],
        "Ironclad Resolve": [
            {"tier": "Heavenly", "ingredients": {"silverleaf herb": 1, "moonlight jade leaf": 1, "spirit spring herb": 1, "crimson flame mushroom": 1, "black iron root": 2}, "qi": 0, "spec": "Perm Str/Vit"}
        ],
        "Tideborn Vigor": [
            {"tier": "Heavenly", "ingredients": {"wild spirit grass": 1, "wild bitter grass": 1, "red ginseng": 1, "silverleaf herb": 1, "mountain green herb": 1, "qi dandelion": 1}, "qi": 0, "spec": "Vit/Str Boost"}
        ],
        "Blazewind Pill": [
            {"tier": "Heavenly", "ingredients": {"crimson flame mushroom": 2, "purple lightning orchid": 3, "wild spirit grass": 1}, "qi": 0, "spec": "Perm Spd/Str"}
        ],
        "Soul Replenishing": [
            {"tier": "Heavenly", "ingredients": {"healing sunflower": 2, "red ginseng": 1, "ironbone grass": 2, "seven star flower": 1}, "qi": 0, "spec": "12% Lifespan (Perm)"}
        ]
    }

# -------------------------------
# LOGIC & INVENTORY
# -------------------------------
db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

with st.sidebar:
    st.markdown("<h1 style='color:#58a6ff;'>📦 Storage</h1>", unsafe_allow_html=True)
    handcrafted = st.toggle("✨ Handcrafted (3x Effect)")
    if st.button("🧹 Clear Inventory"):
        for h in all_herbs: st.session_state[f"i_{h}"] = 0
        st.rerun()
    st.divider()
    search = st.text_input("🔍 Filter Herbs", "")
    inv = {}
    for h in all_herbs:
        val = st.session_state.get(f"i_{h}", 0)
        if search.lower() in h.lower():
            inv[h] = st.number_input(h.title(), min_value=0, value=val, key=f"i_{h}")
        else:
            inv[h] = val

# Calculation Engine
plans, discovery = [], []
total_qi = 0

for name, variants in db.items():
    for v in variants:
        possible = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
        amt = min(possible) if possible else 0
        missing = [ing for ing, req in v["ingredients"].items() if inv.get(ing, 0) < req]
        
        if amt > 0:
            boost_per = v["qi"] * 3 if handcrafted else v["qi"]
            total_qi += (boost_per * amt)
            plans.append({"name": name, "tier": v["tier"], "amt": amt, "qi": boost_per, "spec": v.get("spec"), "ing": v["ingredients"]})
        elif len(missing) == 1:
            m_ing = missing[0]
            discovery.append({"name": name, "tier": v["tier"], "m_name": m_ing, "m_qty": v["ingredients"][m_ing] - inv.get(m_ing, 0)})

# -------------------------------
# DISPLAY
# -------------------------------
st.title("Alchemy Dashboard")
st.markdown("<p style='color:#8b949e;'>Cultivate with maximum efficiency</p>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Stock", sum(inv.values()))
m2.metric("Total Qi potential", f"+{total_qi}%")
m3.metric("Mode", "Handcrafted" if handcrafted else "Standard")
st.divider()

col_main, col_side = st.columns([2, 1])

with col_main:
    if plans:
        for p in sorted(plans, key=lambda x: x['qi'], reverse=True):
            # Benefit Tags
            tags = ""
            if p['qi'] > 0: tags += f'<span class="benefit-tag qi-tag">+{p["qi"]}% Qi Boost</span>'
            if p['spec']: tags += f'<span class="benefit-tag spec-tag">✨ {p["spec"]}</span>'
            
            # Badge & Total logic
            badges = "".join([f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in p["ing"].items()])
            totals = "".join([f'<div style="min-width: 140px; font-size: 0.9rem;">• {ing.title()}: <b>{req*p["amt"]}</b></div>' for ing, req in p["ing"].items()])
            
            # THE RENDER
            html = f"""
            <div class="app-card">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div class="pill-tier">{p['tier']}</div>
                        <div class="pill-title">{p['name']}</div>
                        <div style="margin-top:5px;">{tags}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.7rem; color: #8b949e;">CRAFTABLE</div>
                        <div style="font-size: 2.2rem; color: #58a6ff; font-weight: bold;">{p['amt']}</div>
                    </div>
                </div>
                <div style="margin-top:15px; font-size: 0.8rem; color:#8b949e; font-weight:bold;">RECIPE</div>
                <div style="display: flex; flex-wrap: wrap;">{badges}</div>
                <div class="total-box">
                    <div style="font-size: 0.8rem; color:#58a6ff; font-weight:bold; margin-bottom:8px;">BATCH TOTALS</div>
                    <div style="display: flex; flex-wrap: wrap; gap: 5px 15px;">{totals}</div>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown("<div class='floating-cauldron'>🥣</div>", unsafe_allow_html=True)

with col_side:
    st.subheader("Near Ready")
    for d in discovery[:5]:
        st.markdown(f"""
        <div class="discovery-card">
            <div style="font-size: 0.7rem; color:#8b949e;">{d['tier']}</div>
            <div style="font-weight:bold;">{d['name']}</div>
            <div style="color:#ffab70; font-size:0.85rem;">Missing: {d['m_qty']}x {d['m_name'].title()}</div>
        </div>
        """, unsafe_allow_html=True)
