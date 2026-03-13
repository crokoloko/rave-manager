import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
from PIL import Image

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="TKLZ | MATRIX POS", layout="wide", initial_sidebar_state="collapsed")

# --- STILE MATRIX ---
st.markdown("""
    <style>
    .stApp { background-color: #0a0a0a; color: #ffffff !important; }
    h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stMarkdownContainer"] { 
        color: #ffffff !important; font-family: 'Courier New', monospace !important;
        text-align: center !important; display: flex; justify-content: center; width: 100%;
    }
    [data-testid="stImage"] { display: flex; justify-content: center; padding: 0 !important; margin: -10px 0 -15px 0 !important; }
    .matrix-bar {
        background-color: #000000; border-top: 2px solid #00ff41; border-bottom: 2px solid #00ff41;
        color: #00ff41; padding: 10px 0; font-weight: bold; overflow: hidden; white-space: nowrap; margin-bottom: 15px;
        text-shadow: 0 0 8px #00ff41; display: flex; justify-content: center;
    }
    .matrix-text { display: inline-block; padding-left: 100%; animation: matrix-scroll 80s linear infinite; }
    @keyframes matrix-scroll { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: center; gap: 20px; }
    .stButton>button {
        width: 100%; height: 85px; background: rgba(20, 20, 20, 0.9) !important;
        border: 1px solid #00ff41 !important; color: #ffffff !important; border-radius: 5px !important;
    }
    .strategy-card {
        border: 1px solid #00ff41; padding: 20px; border-radius: 10px; margin: 10px;
        background: rgba(0, 255, 65, 0.1); text-align: center;
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- POESIA MATRIX ---
poesia = "NELLA PENOMBRA DEL MAGAZZINO, TRA I NEON CHE FRIGGONO, I CONTI TORNANO SEMPRE, ANCHE QUANDO I CUORI SI AFFLIGGONO. CIFRE CHE SCORRONO SU VETRI SCURI, SILENZIOSE E AFFILATE, MENTRE FUORI LE OMBRE SI MUOVONO, SU STRADE DIMENTICATE. UN OCCHIO AL TERMINALE, L'ALTRO ALLA PORTA BLINDATA, LA MERCE È VITA, LA CASSA È LA NOSTRA SPADA AFFILATA. NON SERVONO NOMI, NON SERVONO TROPPE PAROLE, QUI IL BUSINESS FIORISCE LONTANO DAL RAGGIO DEL SOLE. UN CLIC, UNA VENDITA, UN ALTRO DROP CHE DECOLLA, MENTRE IL CODICE BRUCIA E LA CITTÀ SI CONTROLLA. UNDERGROUND NEL SANGUE, TK LABS NELLA MENTE, MUOVIAMO IL CAPITALE, RESTANDO NELL'OMBRA, SEGRETAMENTE."
st.markdown(f'<div class="matrix-bar"><div class="matrix-text">*** {poesia} *** {poesia} ***</div></div>', unsafe_allow_html=True)

# --- DATABASE ENGINE ---
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
        tot = sum(next((x['price'] for x in inv if x['id'] == k), 0) * v for k, v in st.session_state.cart.items())
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

@st.fragment
def fragment_stock():
    st.markdown("### 📦 STOCK")
    df_inv = pd.DataFrame(st.session_state.inventory)
    edited = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("💾 SALVA MODIFICHE"):
        st.session_state.inventory = edited.to_dict('records')
        save_all(); st.success("Database Aggiornato"); st.rerun()

@st.fragment
def fragment_analisi():
    st.markdown("### 📈 FINANZA")
    if st.session_state.sales:
        df_s = pd.DataFrame(st.session_state.sales)
        m1, m2 = st.columns(2)
        m1.metric("INCASSI", f"€{df_s['revenue'].sum():.2f}")
        m2.metric("PROFITTO", f"€{df_s['profit'].sum():.2f}")
        st.dataframe(df_s.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else: st.info("Nessun dato.")

@st.fragment
def fragment_strategia():
    st.markdown("### 🧠 PROTOCOLLI ANALITICI")
    inv = st.session_state.inventory
    
    if len(inv) < 1:
        st.info("Aggiungi prodotti nello Stock per sbloccare le strategie.")
        return

    # Calcolo sicuro dei margini
    processed = []
    for i in inv:
        try:
            cost = float(i.get('cost', 0))
            price = float(i.get('price', 0))
            margin = price - cost
            perc = (margin / price * 100) if price > 0 else 0
            processed.append({**i, 'm_perc': perc, 'm_val': margin})
        except: continue

    if not processed: return

    best = max(processed, key=lambda x: x['m_perc'])
    capitale = sum(float(x.get('cost', 0)) * float(x.get('current_qty', 0)) for x in processed)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="strategy-card"><h4>💎 TOP ASSET</h4><p>Il prodotto <b>{best['name']}</b> rende il {best['m_perc']:.1f}% per pezzo.<br>Focus totale su questo per scalare l'investimento.</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="strategy-card"><h4>💰 LIQUIDITÀ</h4><p>Hai <b>€{capitale:.2f}</b> immobilizzati in stock.<br>Trasformali in cassa tramite drop mirati sui social.</p></div>""", unsafe_allow_html=True)
    
    st.markdown("""<div class="strategy-card"><h4>🎯 TATTICA OPERATIVA</h4><p>Applica il bundle: regala un gadget a basso costo per ogni acquisto superiore a 20€. Questo aumenta la velocità di rotazione del magazzino.</p></div>""", unsafe_allow_html=True)

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA", "🧠 STRATEGIA"])
with t1: fragment_cassa()
with t2: fragment_stock()
with t3: fragment_analisi()
with t4: fragment_strategia()
