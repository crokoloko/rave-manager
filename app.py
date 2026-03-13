import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TKLZ | MATRIX POS", layout="wide", initial_sidebar_state="collapsed")

# --- STILE MATRIX TOTALE CENTRATO ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #ffffff !important; }
    
    /* Centratura Universale */
    h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stMarkdownContainer"] { 
        color: #ffffff !important; 
        font-family: 'Courier New', monospace !important;
        text-align: center !important;
        display: flex;
        justify-content: center;
        width: 100%;
    }
    
    /* Logo spacing */
    [data-testid="stImage"] { display: flex; justify-content: center; padding: 0 !important; margin: -10px 0 -15px 0 !important; }
    
    /* BARRA MATRIX CON POESIA */
    .matrix-bar {
        background-color: #000000;
        border-top: 2px solid #00ff41;
        border-bottom: 2px solid #00ff41;
        color: #00ff41;
        padding: 10px 0;
        font-weight: bold;
        font-family: 'Courier New', monospace;
        font-size: 15px;
        overflow: hidden;
        white-space: nowrap;
        margin-bottom: 15px;
        text-shadow: 0 0 8px #00ff41;
        display: flex;
        justify-content: center;
    }
    
    .matrix-text {
        display: inline-block;
        padding-left: 100%;
        animation: matrix-scroll 40s linear infinite, flicker 2s infinite;
    }

    @keyframes matrix-scroll { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
    @keyframes flicker { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }

    /* Centratura Tabs e Contenuto */
    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: center; }
    
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
    }

    /* Bottoni Cassa */
    .stButton>button {
        width: 100%; height: 85px;
        background: rgba(20, 20, 20, 0.9) !important;
        border: 1px solid #00ff41 !important;
        color: #ffffff !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        transition: all 0.2s;
        text-align: center !important;
    }
    .stButton>button:hover { 
        box-shadow: 0 0 15px #00ff41 !important;
        background: #00ff41 !important;
        color: #000000 !important;
    }
    
    /* Metriche Centrate */
    [data-testid="stMetric"] {
        text-align: center !important;
        align-items: center !important;
    }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- INSERIMENTO BARRA MATRIX (POESIA) ---
poesia = (
    "Nella penombra del magazzino, tra i neon che friggono, i conti tornano sempre, anche quando i cuori si affliggono. "
    "Cifre che scorrono su vetri scuri, silenziose e affilate, mentre fuori le ombre si muovono, su strade dimenticate. "
    "Un occhio al terminale, l'altro alla porta blindata, la merce è vita, la cassa è la nostra spada affilata. "
    "Non servono nomi, non servono troppe parole, qui il business fiorisce lontano dal raggio del sole. "
    "Un clic, una vendita, un altro drop che decolla, mentre il codice brucia e la città si controlla. "
    "Underground nel sangue, TK Labs nella mente, muoviamo il capitale, restando nell'ombra, segretamente."
)

st.markdown(f'<div class="matrix-bar"><div class="matrix-text">*** {poesia} *** {poesia} ***</div></div>', unsafe_allow_html=True)

# --- DB ENGINE ---
DB_INV, DB_VEN = "db_inventario.json", "db_vendite.json"

def carica_dati():
    if 'inventory' not in st.session_state:
        if os.path.exists(DB_INV):
            with open(DB_INV, "r") as f: st.session_state.inventory = json.load(f)
        else:
            st.session_state.inventory = [{"id": "k1", "name": "🔥 KIT Leash", "cost": 0.8, "price": 5.0, "current_qty": 400}]
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
    s_save = [dict(x, timestamp=x['timestamp'].isoformat() if isinstance(x['timestamp'], datetime) else x['timestamp']) for x in st.session_state.sales]
    with open(DB_VEN, "w") as f: json.dump(s_save, f)

# --- LOGO ---
try:
    img = Image.open("logo.png")
    _, mid, _ = st.columns([1, 3, 1])
    mid.image(img, use_container_width=True)
except:
    st.markdown("<h1 style='color:#00ff41;'>TKLZ</h1>", unsafe_allow_html=True)

# --- FRAGMENTS ---
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
        tot = sum(next(x['price'] for x in inv if x['id'] == k) * v for k, v in st.session_state.cart.items())
        if st.session_state.cart:
            for id, qta in st.session_state.cart.items():
                p = next((x for x in inv if x['id'] == id), None)
                if p: st.markdown(f"**{qta}x** {p['name']} — **€{p['price']*qta:.2f}**")
            st.divider()
            st.metric("TOTALE", f"€ {tot:.2f}")
            if st.button("✅ CONFERMA", type="primary"):
                for id, qta in st.session_state.cart.items():
                    it = next((x for x in inv if x["id"] == id), None)
                    if it:
                        it["current_qty"] -= qta
                        st.session_state.sales.append({"timestamp": datetime.now(), "product": it["name"], "qta": qta, "revenue": it["price"]*qta, "profit": (it["price"]-it["cost"])*qta})
                save_all(); st.session_state.cart = {}; st.toast("OK ⚡"); st.rerun()
            if st.button("🗑️ SVUOTA"): st.session_state.cart = {}; st.rerun()
        else: st.markdown("_Carrello vuoto_")

@st.fragment
def fragment_stock():
    st.markdown("### 📦 STOCK")
    df_inv = pd.DataFrame(st.session_state.inventory)
    edited = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    if c1.button("💾 SALVA"):
        st.session_state.inventory = edited.to_dict('records')
        save_all(); st.success("Salvato"); st.rerun()
    if c2.button("⚠️ RESET DB"):
        if os.path.exists(DB_INV): os.remove(DB_INV)
        if os.path.exists(DB_VEN): os.remove(DB_VEN)
        st.session_state.clear(); st.rerun()

@st.fragment
def fragment_analisi():
    st.markdown("### 📈 ANALISI FINANZIARIA")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        m1, m2 = st.columns(2)
        m1.metric("INCASSI", f"€{df_s['revenue'].sum():.2f}")
        m2.metric("PROFITTO", f"€{df_s['profit'].sum():.2f}")
        st.dataframe(df_s.sort_index(ascending=False), use_container_width=True, hide_index=True)
        st.divider()
        st.markdown("#### ⚙️ PANNELLO CONTROLLO")
        csv_data = df_s.to_csv(index=False).encode('utf-8')
        col_exp, col_res = st.columns(2)
        with col_exp:
            st.download_button(label="📥 SCARICA CSV", data=csv_data, file_name=f"report.csv", mime='text/csv', use_container_width=True)
        with col_res:
            if st.button("💀 AZZERA VENDITE", use_container_width=True):
                st.session_state.sales = []
                if os.path.exists(DB_VEN): os.remove(DB_VEN)
                st.rerun()
    else: st.info("Nessuna vendita.")

# --- TABS ---
t1, t2, t3 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA"])
with t1: fragment_cassa()
with t2: fragment_stock()
with t3: fragment_analisi()
