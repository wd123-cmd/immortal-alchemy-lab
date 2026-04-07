import streamlit as st

# -------------------------------
# APP CONFIG & THEME
# -------------------------------
st.set_page_config(layout="wide", page_title="Immortal Alchemy Lab", page_icon="🧿")

st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #1a1f35, #0a0c10); }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .app-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 22px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 25px;
    }
    .pill-title { color: #58a6ff; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .pill-tier { color: #8b949e; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px; }
    .pill-effect { color: #3fb950; font-weight: 500; font-size: 1.1rem; margin-top: 5px; }
    .badge {
        display: inline-block;
        background: rgba(88, 166, 255, 0.08);
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
        padding: 12px;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 12px;
        border: 1px dashed rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------
# DATASET (Audited Recipes)
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
            {"tier": "Heavenly", "ingredients": {"blue wave coral herb": 2, "silverleaf herb": 1, "spirit spring herb": 1, "ironbone grass": 2}, "qi": 168}
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
# APP LOGIC
# -------------------------------
db = get_db()
all_herbs = sorted(list(set(h for v_list in db.values() for v in v_list for h in v["ingredients"])))

with st.sidebar:
    st.markdown("<h1 style='color:#58a6ff;'>📦 Storage</h1>", unsafe_allow_html=True)
    handcrafted = st.toggle("✨ Handcrafted (3x Effect)")
    if st.button("🧹 Clear All"):
        for h in all_herbs: st.session_state[f"i_{h}"] = 0
    st.divider()
    search = st.text_input("🔍 Search herbs...", "")
    inv = {h: st.number_input(h.title(), min_value=0, key=f"i_{h}") if search.lower() in h.lower() else st.session_state.get(f"i_{h}", 0) for h in all_herbs}

# Main UI
st.markdown("<h1 style='color:white;'>Alchemy Dashboard</h1>", unsafe_allow_html=True)
m1, m2 = st.columns(2)
m1.metric("Items in Stock", sum(inv.values()))
m2.metric("Handcrafted Mode", "ON" if handcrafted else "OFF")
st.divider()

plans = []
for name, variants in db.items():
    for v in variants:
        amt = min([inv.get(ing, 0) // req for ing, req in v["ingredients"].items()])
        if amt > 0:
            plans.append({"name": name, "tier": v["tier"], "amt": amt, "qi": v["qi"], "spec": v.get("spec"), "ing": v["ingredients"]})

if plans:
    for p in sorted(plans, key=lambda x: x['qi'], reverse=True):
        val = p['qi'] * 3 if handcrafted else p['qi']
        effect_str = f"+{val}% Qi Boost" if val > 0 else p['spec']
        
        st.markdown(f"""
        <div class="app-card">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <p class="pill-tier">{p['tier']}</p>
                    <p class="pill-title">{p['name']}</p>
                    <p class="pill-effect">✨ {effect_str}</p>
                </div>
                <div style="text-align: right;">
                    <p style="font-size: 0.8rem; color: #8b949e; margin:0;">CRAFTABLE</p>
                    <p style="font-size: 2.2rem; color: #58a6ff; font-weight: bold; margin:0;">{p['amt']}</p>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <p style="font-size: 0.75rem; color: #8b949e; margin-bottom: 5px;">BASE RECIPE (PER PILL)</p>
                {" ".join([f'<span class="badge">{ing.title()}: {req}</span>' for ing, req in p["ing"].items()])}
            </div>
            
            <div class="total-box">
                <p style="font-size: 0.75rem; color: #58a6ff; margin-bottom: 8px; font-weight: bold; letter-spacing: 1px;">TOTAL MATERIALS FOR {p['amt']}x CRAFT</p>
                <div style="display: flex; flex-wrap: wrap; gap: 15px;">
                    {" ".join([f'<div style="font-size: 0.9rem; color: white;">• {ing.title()}: <b>{req * p["amt"]}</b></div>' for ing, req in p["ing"].items()])}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("<div style='text-align: center; opacity: 0.5; padding: 50px;'><p style='font-size: 4rem;'>🥣</p><p>Add ingredients to begin brewing.</p></div>", unsafe_allow_html=True)
