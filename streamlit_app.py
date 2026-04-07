import streamlit as st

# -------------------------------
# APP CONFIG & NATIVE APP STYLING
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

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
    }
    
    .pill-title { color: #58a6ff; font-size: 1.6rem; font-weight: 700; margin: 0; }
    .pill-tier { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 4px; }
    
    /* Benefit Styling */
    .benefit-tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 6px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-right: 8px;
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
# CORE LOGIC
# -------------------------------
db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

with st.sidebar:
    st.markdown("<h1 style='color:#58a6ff;'>📦 Storage</h1>", unsafe_allow_html=True)
    handcrafted = st.toggle("✨ Handcrafted (3x Effect)")
    
    if st.button("🧹 Clear All Inventory"):
        for h in all_herbs: st.session_state[f"i_{h}"] = 0
        st.rerun()
        
    st.divider()
    search = st.text_input("🔍 Filter Chest Items", "")
    
    inv = {}
    for h in all_herbs:
        val = st.session_state.get(f"i_{h}", 0)
        if search.lower() in h.lower():
            inv[h] = st.number_input(h.title(), min_value=0, value=val, key=f"i_{h}")
        else:
            inv[h] = val

# Calculation
plans = []
discovery = []
total_qi_potential = 0

for name, variants in db.items():
    for v in variants:
        possible_crafts = [inv.get(ing, 0) // req for ing, req in v["ingredients"].items()]
        amt = min(possible_crafts) if possible_crafts else 0
        
        missing = []
        for ing, req in v["ingredients"].items():
            if inv.get(ing, 0) < req:
                missing.append({"name": ing, "needed": req - inv.get(ing, 0)})
        
        if amt > 0:
            boost = v["qi"] * 3 if handcrafted else v["qi"]
            total_qi_potential += (boost * amt)
            plans.append({"name": name, "tier": v["tier"], "amt": amt, "qi": v["qi"], "spec": v.get("spec"), "ing": v["ingredients"]})
        elif len(missing) == 1:
            discovery.append({"name": name, "tier": v["tier"], "missing": missing[0]})

# -------------------------------
# UI LAYOUT
# -------------------------------
st.markdown("<h1 style='color:white; margin-bottom: 0;'>Alchemy Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#8b949e; margin-bottom: 20px;'>Maximize your cultivation efficiency</p>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Stockpile Items", sum(inv.values()))
m2.metric("Total Qi Potential", f"+{total_qi_potential}%")
m3.metric("Mode", "Handcrafted" if handcrafted else "Standard")
st.divider()

col_main, col_side = st.columns([2, 1])

with col_main:
    if plans:
        for p in sorted(plans, key=lambda x: x['qi'], reverse=True):
            # Calculate Benefits
            val = p['qi'] * 3 if handcrafted else p['qi']
            benefit_html = ""
            if val > 0:
                benefit_html += f'<span class="benefit-tag qi-tag">+{val}% Qi Boost</span>'
            if p.get('spec'):
                benefit_html += f'<span class="benefit-tag spec-tag">✨ {p["spec"]}</span>'
            
            badges_html = "".join([f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in p["ing"].items()])
            totals_html = "".join([f'<div style="font-size: 0.95rem; color: #f0f6fc; min-width: 150px;">• {ing.title()}: <b>{req * p["amt"]}</b></div>' for ing, req in p["ing"].items()])
            
            st.markdown(f"""<div class="app-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <p class="pill-tier">{p['tier']}</p>
                        <p class="pill-title">{p['name']}</p>
                        <div style="margin-top: 8px;">{benefit_html}</div>
                    </div>
                    <div style="text-align: right;">
                        <p style="font-size: 0.8rem; color: #8b949e; margin:0;">CRAFTABLE</p>
                        <p style="font-size: 2.5rem; color: #58a6ff; font-weight: bold; margin:0;">{p['amt']}</p>
                    </div>
                </div>
                
                <div style="margin-top: 18px;">
                    <p style="font-size: 0.75rem; color: #8b949e; margin-bottom: 5px; font-weight: bold;">BASE RECIPE (PER PILL)</p>
                    <div style="flex-wrap: wrap; display: flex;">{badges_html}</div>
                </div>

                <div class="total-box">
                    <p style="font-size: 0.8rem; color: #58a6ff; margin-bottom: 10px; font-weight: bold;">BATCH SUMMARY ({p['amt']} PILLS)</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px 20px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px; margin-bottom: 10px;">
                        {totals_html}
                    </div>
                    <p style="font-size: 0.85rem; color: #3fb950; margin:0;">Total Batch Gain: <b>+{val * p['amt']}% Qi Potential</b></p>
                </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("<div class='floating-cauldron'>🥣</div><p style='text-align:center; color:#8b949e;'>Cauldron Empty. Add ingredients.</p>", unsafe_allow_html=True)

with col_side:
    st.markdown("### 🧪 Near Completion")
    if discovery:
        for d in discovery[:6]:
            st.markdown(f"""<div class="discovery-card">
                <p style="margin:0; font-size: 0.7rem; color: #8b949e; text-transform: uppercase;">{d['tier']}</p>
                <p style="margin:0; font-weight: bold; color: #f0f6fc; font-size: 1rem;">{d['name']}</p>
                <p style="margin-top:5px; font-size: 0.85rem; color: #ffab70;">Missing: <b>{d['missing']['needed']}x {d['missing']['name'].title()}</b></p>
            </div>""", unsafe_allow_html=True)
    else:
        st.write("No near-complete recipes.")
