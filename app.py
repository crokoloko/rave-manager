import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TKLZ | TURBO POS", layout="wide", initial_sidebar_state="collapsed")

# --- STILE OTTIMIZZATO & MARQUEE ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #ffffff !important; }
    h1, h2, h3, h4, p, label, .stMarkdown { color: #ffffff !important; font-family: 'Courier New', monospace !important; }
    
    /* Logo spacing */
    [data-testid="stImage"] { display: flex; justify-content: center; padding: 0 !important; margin: -10px 0 -15px 0 !important; }
    
    /* BARRA SCORREVOLE GIALLA */
    .marquee-container {
        background-color: #ffff00;
        color: #000000;
        padding: 5px 0;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        overflow: hidden;
        white-space: nowrap;
        position: relative;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    .marquee-text {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 15s linear infinite;
    }
    @keyframes marquee {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-100%, 0); }
    }

    /* Bottoni Cassa */
    .stButton>button {
        width: 100%; height: 80px;
        background: rgba(35, 35, 35, 0.9) !important;
        border: 1px solid #444 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: bold !important; font-size: 16px !important;
        transition: transform 0.1s;
    }
    .stButton>button:active { transform: scale(0.95); }
    .stButton>button:hover { border-color: #ff00ff !important; box-shadow: 0 0 15px #ff00ff !important; }
    
    div.stButton > button[kind="primary"] { 
        background: rgba(48, 209, 88, 0.3) !important; 
        border: 2px solid #30d158 !important; 
    }
    
    .btn-reset > div > button {
        background: rgba(255, 69, 58, 0.2) !important;
        border: 1px solid #ff453a !important;
        color: #ff453a !important;
        height: 50px !important;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- INSERIMENTO BARRA SCORREVOLE ---
st.markdown('<div class="marquee-container"><div class="marquee-text">SESSO , DROGA E NUN CAGAR U CAZZ! — SESSO , DROGA E NUN CAGAR U CAZZ! — SESSO , DROGA E NUN CAGAR U CAZZ!</div></div>', unsafe_allow_html=True)

# --- DATABASE ENGINE ---
DB_INV = "db_inventario.json"
DB_VEN = "db_vendite.json"

def carica_dati():
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

carica_dati()

if 'cart' not in st.session_state: st.session_state.cart = {}

def save_all():
    with open(DB_INV, "w") as f: json.dump(st.session_state.inventory, f)
    sales_to_save = [dict(x, timestamp=x['timestamp'].isoformat() if isinstance(x['timestamp'], datetime) else x['timestamp']) for x in st.session_state.sales]
    with open(DB_VEN, "w") as f: json.dump(sales_to_save, f)

# --- LOGO ---
try:
    img = Image.open("logo.png")
    _, mid, _ = st.columns([1, 3, 1])
    mid.image(img, use_container_width=True)
except:
    st.markdown("<h1 style='text-align:center; color:#ff00ff;'>TKLZ</h1>", unsafe_allow_html=True)

# --- UI COMPONENTS ---

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
                        st.rerun()
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
            if st.button("🗑️ SVUOTA", use_container_width=True):
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
    if c_r.button("⚠️ RESET DATABASE", use_container_width=True):
        if os.path.exists(DB_INV): os.remove(DB_INV)
        if os.path.exists(DB_VEN): os.remove(DB_VEN)
        st.session_state.clear()
        st.rerun()

@st.fragment
def fragment_analisi():
    st.markdown("### 📈 ANALISI RENDIMENTO")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        m1, m2 = st.columns(2)
        m1.metric("INCASSI TOTALI", f"€{df_s['revenue'].sum():.2f}")
        m2.metric("PROFITTO NETTO", f"€{df_s['profit'].sum():.2f}")
        st.dataframe(df_s.sort_index(ascending=False), use_container_width=True, hide_index=True)
        st.divider()
        st.markdown("#### ⚙️ AZIONI REPORT")
        col_exp, col_res = st.columns(2)
        with col_exp:
            csv = df_s.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 ESPORTA REPORT .CSV", data=csv, file_name=f"report_tklz_{datetime.now().strftime('%d_%m_%Y')}.csv", mime="text/csv", use_container_width=True)
        with col_res:
            st.markdown('<div class="btn-reset">', unsafe_allow_html=True)
            if st.button("💀 AZZERA DATI VENDITE", use_container_width=True):
                st.session_state.sales = []
                if os.path.exists(DB_VEN): os.remove(DB_VEN)
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    else: st.info("Nessuna vendita registrata.")

# --- TABS ---
t1, t2, t3 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA"])
with t1: fragment_cassa()
with t2: fragment_stock()
with t3: fragment_analisi()
