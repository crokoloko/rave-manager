import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TKLZ | POS", layout="wide", initial_sidebar_state="collapsed")

# --- STILE NEON & LEGGIBILITÀ ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #ffffff !important; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #ffffff !important; font-family: 'Courier New', monospace !important; }
    
    /* Logo spacing */
    [data-testid="stImage"] { display: flex; justify-content: center; padding: 0 !important; margin: -25px 0 -15px 0 !important; }

    /* Bottoni Cassa - TESTO BIANCO SEMPRE */
    .stButton>button {
        width: 100%; height: 110px;
        background: rgba(35, 35, 35, 0.9) !important;
        border: 1px solid #444 !important;
        color: #ffffff !important;
        border-radius: 15px !important;
        font-weight: bold !important; font-size: 18px !important;
        transition: all 0.3s; text-transform: uppercase;
    }
    .stButton>button:hover { border-color: #ff00ff !important; box-shadow: 0 0 20px #ff00ff !important; color: #ffffff !important; }

    /* Bottone Conferma Verde */
    div.stButton > button[kind="primary"] { background: rgba(48, 209, 88, 0.3) !important; border: 2px solid #30d158 !important; color: #ffffff !important; }
    div.stButton > button[kind="primary"]:hover { background: #30d158 !important; color: #000 !important; }

    /* Metriche Neon */
    [data-testid="stMetricValue"] { color: #00ffbc !important; }
    [data-testid="stMetricLabel"] { color: #ffffff !important; }
    
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ---
DB_INV = "db_inventario.json"
DB_VEN = "db_vendite.json"

def carica_db():
    if 'inventory' not in st.session_state:
        if os.path.exists(DB_INV):
            with open(DB_INV, "r") as f: st.session_state.inventory = json.load(f)
        else:
            st.session_state.inventory = [
                {"id": "k1", "name": "🔥 KIT Leash", "cost": 0.8, "price": 5.0, "current_qty": 400},
                {"id": "b1", "name": "🍺 Birra", "cost": 1.0, "price": 5.0, "current_qty": 200}
            ]
    if 'sales' not in st.session_state:
        if os.path.exists(DB_VEN):
            with open(DB_VEN, "r") as f:
                v = json.load(f)
                for x in v: x['timestamp'] = datetime.fromisoformat(x['timestamp'])
                st.session_state.sales = v
        else: st.session_state.sales = []

carica_db()

# --- LOGICA VENDITA ---
if 'cart' not in st.session_state: st.session_state.cart = {}

def add_to_cart(id): st.session_state.cart[id] = st.session_state.cart.get(id, 0) + 1

def checkout():
    for id, qta in st.session_state.cart.items():
        it = next((x for x in st.session_state.inventory if x["id"] == id), None)
        if it and it["current_qty"] >= qta:
            it["current_qty"] -= qta
            rev = it["price"] * qta
            st.session_state.sales.append({
                "timestamp": datetime.now().isoformat(), "product": it["name"],
                "qta": qta, "revenue": rev, "profit": rev - (it["cost"] * qta)
            })
    with open(DB_INV, "w") as f: json.dump(st.session_state.inventory, f)
    with open(DB_VEN, "w") as f: 
        s_save = [dict(x, timestamp=str(x['timestamp'])) if isinstance(x['timestamp'], datetime) else x for x in st.session_state.sales]
        json.dump(s_save, f)
    st.session_state.cart = {}
    st.toast("PAGATO ⚡")

# --- UI ---
try:
    img = Image.open("logo.png")
    _, mid, _ = st.columns([1, 4, 1])
    mid.image(img, use_container_width=True)
except:
    st.markdown("<h1 style='text-align:center; color:#ff00ff;'>TKLZ</h1>", unsafe_allow_html=True)

t1, t2, t3 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA"])

with t1:
    c_l, c_r = st.columns([6, 4])
    with c_l:
        st.markdown("### 🛒 SHOP")
        inv = st.session_state.inventory
        for i in range(0, len(inv), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(inv):
                    p = inv[i + j]
                    # CHIAVE UNICA PROTETTA: id + indice
                    if cols[j].button(f"{p['name']}\n€{p['price']:.2f}", key=f"btn_{p['id']}_{i+j}"):
                        add_to_cart(p['id'])
                        st.rerun()
    with c_r:
        st.markdown("### 🧾 ORDINE")
        tot = 0.0
        for id, qta in st.session_state.cart.items():
            p = next((x for x in inv if x['id'] == id), None)
            if p:
                sub = p['price'] * qta
                tot += sub
                st.write(f"**{qta}x** {p['name']} — **€{sub:.2f}**")
        st.divider()
        st.metric("TOTALE", f"€ {tot:.2f}")
        if st.button("✅ CONFERMA", type="primary", use_container_width=True): checkout(); st.rerun()
        if st.button("🗑️ SVUOTA", use_container_width=True): st.session_state.cart = {}; st.rerun()

with t2:
    st.markdown("### 📦 STOCK")
    df_inv = pd.DataFrame(st.session_state.inventory)
    edited = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 SALVA STOCK", type="primary", use_container_width=True):
        st.session_state.inventory = edited.to_dict('records')
        with open(DB_INV, "w") as f: json.dump(st.session_state.inventory, f)
        st.success("Salvo!")
        st.rerun()

with t3:
    st.markdown("### 📈 ANALISI")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        c_a, c_b = st.columns(2)
        c_a.metric("INCASSI", f"€{sum(x['revenue'] for x in st.session_state.sales):.2f}")
        c_b.metric("PROFITTO", f"€{sum(x['profit'] for x in st.session_state.sales):.2f}")
        st.dataframe(df_s, use_container_width=True)
        csv = df_s.to_csv(index=False).encode('utf-8')
        st.download_button("📥 SCARICA REPORT", data=csv, file_name="report.csv", use_container_width=True)
    else: st.info("Nessun dato")
