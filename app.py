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
    h1, h2, h3, h4, p, label, .stMarkdown, [data-testid="stMarkdownContainer"] { 
        color: #ffffff !important; 
        font-family: 'Courier New', monospace !important;
        text-align: center !important;
        display: flex; justify-content: center; width: 100%;
    }
    [data-testid="stImage"] { display: flex; justify-content: center; padding: 0 !important; margin: -10px 0 -15px 0 !important; }
    
    .matrix-bar {
        background-color: #000000; border-top: 2px solid #00ff41; border-bottom: 2px solid #00ff41;
        color: #00ff41; padding: 10px 0; font-weight: bold; font-family: 'Courier New', monospace;
        font-size: 15px; overflow: hidden; white-space: nowrap; margin-bottom: 15px;
        text-shadow: 0 0 8px #00ff41; display: flex; justify-content: center;
    }
    .matrix-text { display: inline-block; padding-left: 100%; animation: matrix-scroll 80s linear infinite, flicker 2s infinite; }
    @keyframes matrix-scroll { 0% { transform: translate(0, 0); } 100% { transform: translate(-100%, 0); } }
    @keyframes flicker { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }

    .stTabs [data-baseweb="tab-list"] { display: flex; justify-content: center; gap: 20px; }
    .stButton>button {
        width: 100%; height: 85px; background: rgba(20, 20, 20, 0.9) !important;
        border: 1px solid #00ff41 !important; color: #ffffff !important;
        border-radius: 5px !important; font-weight: bold !important; transition: all 0.2s;
    }
    .stButton>button:hover { box-shadow: 0 0 15px #00ff41 !important; background: #00ff41 !important; color: #000000 !important; }
    
    .strategy-card {
        border: 1px solid #00ff41; padding: 20px; border-radius: 10px; margin: 10px;
        background: rgba(0, 255, 65, 0.1); box-shadow: 0 0 10px rgba(0, 255, 65, 0.2);
    }
    .margin-high { color: #00ff41; font-weight: bold; }
    .margin-low { color: #ff453a; font-weight: bold; }

    header {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- POESIA MAIUSCOLA ---
poesia = "NELLA PENOMBRA DEL MAGAZZINO, TRA I NEON CHE FRIGGONO, I CONTI TORNANO SEMPRE, ANCHE QUANDO I CUORI SI AFFLIGGONO. CIFRE CHE SCORRONO SU VETRI SCURI, SILENZIOSE E AFFILATE, MENTRE FUORI LE OMBRE SI MUOVONO, SU STRADE DIMENTICATE. UN OCCHIO AL TERMINALE, L'ALTRO ALLA PORTA BLINDATA, LA MERCE È VITA, LA CASSA È LA NOSTRA SPADA AFFILATA. NON SERVONO NOMI, NON SERVONO TROPPE PAROLE, QUI IL BUSINESS FIORISCE LONTANO DAL RAGGIO DEL SOLE. UN CLIC, UNA VENDITA, UN ALTRO DROP CHE DECOLLA, MENTRE IL CODICE BRUCIA E LA CITTÀ SI CONTROLLA. UNDERGROUND NEL SANGUE, TK LABS NELLA MENTE, MUOVIAMO IL CAPITALE, RESTANDO NELL'OMBRA, SEGRETAMENTE."
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
        csv_data = df_s.to_csv(index=False).encode('utf-8')
        st.download_button("📥 REPORT CSV", data=csv_data, file_name="report.csv", mime='text/csv', use_container_width=True)
    else: st.info("Nessun dato.")

@st.fragment
def fragment_strategia():
    st.markdown("### 🧠 ANALISI STRATEGICA REAL-TIME")
    inv = st.session_state.inventory
    
    if not inv:
        st.warning("Inventario vuoto. Impossibile calcolare strategie.")
        return

    # Calcolo Margini
    for item in inv:
        item['margin_val'] = item['price'] - item['cost']
        item['margin_perc'] = (item['margin_val'] / item['price'] * 100) if item['price'] > 0 else 0

    best_margin = max(inv, key=lambda x: x['margin_perc'])
    worst_margin = min(inv, key=lambda x: x['margin_perc'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="strategy-card">
            <h4>💎 IL TUO ASSET D'ORO</h4>
            <p>Il prodotto <b>{best_margin['name']}</b> ha il margine più alto ({best_margin['margin_perc']:.1f}%).<br>
            <b>STRATEGIA:</b> Spingilo come 'prodotto civetta'. Ogni volta che ne vendi uno, il tuo investimento cresce velocemente.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="strategy-card">
            <h4>🛠️ OTTIMIZZAZIONE PREZZI</h4>
            <p>L'oggetto <b>{worst_margin['name']}</b> rende solo il {worst_margin['margin_perc']:.1f}%.<br>
            <b>STRATEGIA:</b> Se è un prodotto ad alta rotazione, lascialo così. Se vende poco, alza il prezzo di almeno 1€ per coprire i costi operativi.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Calcolo Bundling suggerito
        st.markdown(f"""
        <div class="strategy-card">
            <h4>📦 PROTOCOLLO COMBO</h4>
            <p>Crea un bundle tra <b>{best_margin['name']}</b> e un altro oggetto.<br>
            <b>LOGICA:</b> Usare l'alto margine del primo per assorbire un piccolo sconto sul secondo, aumentando il volume totale di cassa.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Analisi Capitale
        capitale_bloccato = sum(item['cost'] * item['current_qty'] for item in inv)
        st.markdown(f"""
        <div class="strategy-card">
            <h4>💰 STATO DEL PORTAFOGLIO</h4>
            <p>Hai attualmente <b>€{capitale_bloccato:.2f}</b> di capitale bloccato in magazzino.<br>
            <b>OBIETTIVO:</b> Trasformare questo stock in liquidità entro le prossime 48 ore tramite i 'Drop' online.</p>
        </div>
        """, unsafe_allow_html=True)

# --- TABS ---
t1, t2, t3, t4 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA", "🧠 STRATEGIA"])
with t1: fragment_cassa()
with t2: fragment_stock()
with t3: fragment_analisi()
with t4: fragment_strategia()
