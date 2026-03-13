import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TKLZ | TURBO POS", layout="wide", initial_sidebar_state="collapsed")

# --- STILE OTTIMIZZATO ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #ffffff !important; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #ffffff !important; font-family: 'Courier New', monospace !important; }
    [data-testid="stImage"] { display: flex; justify-content: center; padding: 0 !important; margin: -25px 0 -15px 0 !important; }
    .stButton>button {
        width: 100%; height: 100px;
        background: rgba(35, 35, 35, 0.9) !important;
        border: 1px solid #444 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: bold !important; font-size: 18px !important;
        transition: transform 0.1s;
    }
    .stButton>button:active { transform: scale(0.95); }
    .stButton>button:hover { border-color: #ff00ff !important; box-shadow: 0 0 15px #ff00ff !important; }
    div.stButton > button[kind="primary"] { background: rgba(48, 209, 88, 0.3) !important; border: 2px solid #30d158 !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE ENGINE (CON CACHE) ---
DB_INV = "db_inventario.json"
DB_VEN = "db_vendite.json"

def carica_dati_fissi():
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
                for x in v: 
                    if isinstance(x['timestamp'], str): x['timestamp'] = datetime.fromisoformat(x['timestamp'])
                st.session_state.sales = v
        else: st.session_state.sales = []

carica_dati_fissi()

if 'cart' not in st.session_state: st.session_state.cart = {}

# --- LOGICA SALVATAGGIO ---
def save_all():
    with open(DB_INV, "w") as f: json.dump(st.session_state.inventory, f)
    sales_to_save = [dict(x, timestamp=x['timestamp'].isoformat() if isinstance(x['timestamp'], datetime) else x['timestamp']) for x in st.session_state.sales]
    with open(DB_VEN, "w") as f: json.dump(sales_to_save, f)

# --- UI COMPONENTS ---
def show_logo():
    try:
        img = Image.open("logo.png")
        _, mid, _ = st.columns([1, 3, 1])
        mid.image(img, use_container_width=True)
    except:
        st.markdown("<h1 style='text-align:center; color:#ff00ff;'>TKLZ</h1>", unsafe_allow_html=True)

show_logo()

# --- FRAGMENTS (Rendono l'app scattante) ---

@st.fragment
def fragment_cassa():
    c_l, c_r = st.columns([6, 4])
    inv = st.session_state.inventory
    
    with c_l:
        st.markdown("### 🛒 SHOP")
        for i in range(0, len(inv), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(inv):
                    p = inv[i + j]
                    if cols[j].button(f"{p['name']}\n€{p['price']:.2f}", key=f"p_{p['id']}"):
                        st.session_state.cart[p['id']] = st.session_state.cart.get(p['id'], 0) + 1
                        st.rerun() # Ricarica solo questo frammento
    
    with c_r:
        st.markdown("### 🧾 ORDINE")
        tot = 0.0
        if st.session_state.cart:
            for id, qta in st.session_state.cart.items():
                p = next((x for x in inv if x['id'] == id), None)
                if p:
                    sub = p['price'] * qta
                    tot += sub
                    st.write(f"**{qta}x** {p['name']} — **€{sub:.2f}**")
            st.divider()
            st.metric("TOTALE", f"€ {tot:.2f}")
            if st.button("✅ CONFERMA PAGAMENTO", type="primary", use_container_width=True):
                for id, qta in st.session_state.cart.items():
                    it = next((x for x in st.session_state.inventory if x["id"] == id), None)
                    if it:
                        it["current_qty"] -= qta
                        st.session_state.sales.append({
                            "timestamp": datetime.now(), "product": it["name"],
                            "qta": qta, "revenue": it["price"] * qta, "profit": (it["price"] - it["cost"]) * qta
                        })
                save_all()
                st.session_state.cart = {}
                st.toast("PAGATO ⚡")
                st.rerun()
            if st.button("🗑️ SVUOTA CARRELLO", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
        else: st.info("Seleziona prodotti")

@st.fragment
def fragment_stock():
    st.markdown("### 📦 STOCK")
    df_inv = pd.DataFrame(st.session_state.inventory)
    edited = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    c_s, c_r = st.columns(2)
    if c_s.button("💾 SALVA MODIFICHE", type="primary", use_container_width=True):
        st.session_state.inventory = edited.to_dict('records')
        save_all()
        st.success("Fatto!")
    
    if c_r.button("⚠️ RESET TOTALE", use_container_width=True):
        if os.path.exists(DB_INV): os.remove(DB_INV)
        if os.path.exists(DB_VEN): os.remove(DB_VEN)
        st.session_state.clear()
        st.rerun()

# --- MAIN TABS ---
t1, t2, t3 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 ANALISI"])

with t1: fragment_cassa()
with t2: fragment_stock()
with t3:
    st.markdown("### 📈 ANALISI")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        st.metric("INCASSI TOTALI", f"€{df_s['revenue'].sum():.2f}")
        st.dataframe(df_s, use_container_width=True, hide_index=True)
        st.download_button("📥 EXPORT CSV", data=df_s.to_csv(index=False), file_name="report.csv", use_container_width=True)
    else: st.info("Nessun dato")
