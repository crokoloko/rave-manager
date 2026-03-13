import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
import json
import os
from PIL import Image

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="TKLZ | UNDERGROUND POS",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TEMA CYBER-PUNK & NEON (CSS AVANZATO) ---
st.markdown("""
    <style>
    /* Sfondo e Font Generale */
    .stApp {
        background-color: #0a0a0a;
        color: #e0e0e0;
    }
    
    /* Titoli e Testi */
    h1, h2, h3, h4, p {
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Rimozione spazi vuoti intorno al Logo */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        padding: 0 !important;
        margin: -20px 0 -10px 0 !important; /* Riduce i margini sopra e sotto */
    }

    /* Pulsanti Prodotto - Effetto Neon Glow */
    .stButton>button {
        width: 100%;
        height: 110px;
        background: rgba(30, 30, 30, 0.6) !important;
        border: 1px solid #444 !important;
        color: #00ffbc !important; /* Colore base Neon Cyan/Verde */
        border-radius: 15px !important;
        font-weight: bold !important;
        transition: all 0.3s ease-in-out !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton>button:hover {
        border-color: #ff00ff !important; /* Cambia in Rosa Fluo su hover */
        box-shadow: 0 0 15px #ff00ff, inset 0 0 5px #ff00ff !important;
        transform: scale(1.02);
        color: #ffffff !important;
    }

    /* Bottone Paga - Verde Tossico */
    div.stButton > button[kind="primary"] {
        background: rgba(48, 209, 88, 0.2) !important;
        border: 2px solid #30d158 !important;
        color: #30d158 !important;
        box-shadow: 0 0 10px rgba(48, 209, 88, 0.4) !important;
    }
    
    div.stButton > button[kind="primary"]:hover {
        background: #30d158 !important;
        color: #000 !important;
        box-shadow: 0 0 25px #30d158 !important;
    }

    /* Carrello Glassmorphism */
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Tabs Style */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #1a1a1a !important;
        border-radius: 10px 10px 0 0 !important;
        color: #888 !important;
        border: none !important;
    }

    .stTabs [aria-selected="true"] {
        color: #ff00ff !important;
        border-bottom: 2px solid #ff00ff !important;
    }

    /* Nasconde Header Streamlit */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA DATABASE ---
VALUTA_SIMBOLO = "€"
DB_INVENTARIO = "db_inventario.json"
DB_VENDITE = "db_vendite.json"

def salva_db_inventario():
    with open(DB_INVENTARIO, "w", encoding="utf-8") as f:
        json.dump(st.session_state.inventory_list, f, indent=4, ensure_ascii=False)

def salva_db_vendite():
    vendite_serializzabili = []
    for v in st.session_state.sales_history:
        v_copy = v.copy()
        if isinstance(v_copy['timestamp'], datetime):
            v_copy['timestamp'] = v_copy['timestamp'].isoformat()
        vendite_serializzabili.append(v_copy)
    with open(DB_VENDITE, "w", encoding="utf-8") as f:
        json.dump(vendite_serializzabili, f, indent=4, ensure_ascii=False)

def carica_db():
    if os.path.exists(DB_INVENTARIO):
        with open(DB_INVENTARIO, "r", encoding="utf-8") as f:
            st.session_state.inventory_list = json.load(f)
    else:
        st.session_state.inventory_list = [
            {"id": "kit-1", "name": "🔥 KIT Leash", "cost": 0.80, "price": 5.0, "initial_qty": 400, "current_qty": 400, "is_bundle": False},
            {"id": "drink-1", "name": "🍺 Birra", "cost": 1.00, "price": 5.0, "initial_qty": 200, "current_qty": 200, "is_bundle": False}
        ]
        salva_db_inventario()

    if os.path.exists(DB_VENDITE):
        with open(DB_VENDITE, "r", encoding="utf-8") as f:
            vendite = json.load(f)
            for v in vendite: v['timestamp'] = datetime.fromisoformat(v['timestamp'])
            st.session_state.sales_history = vendite
    else:
        st.session_state.sales_history = []
        salva_db_vendite()

if 'db_caricato' not in st.session_state:
    carica_db()
    st.session_state.db_caricato = True

if 'carrello' not in st.session_state:
    st.session_state.carrello = {}

# --- FUNZIONI OPERATIVE ---
def aggiungi_al_carrello(item_id):
    st.session_state.carrello[item_id] = st.session_state.carrello.get(item_id, 0) + 1

def registra_vendita():
    if not st.session_state.carrello: return
    successo = True
    for item_id, qta in st.session_state.carrello.items():
        item = next((i for i in st.session_state.inventory_list if i["id"] == item_id), None)
        if item and item["current_qty"] >= qta:
            item["current_qty"] -= qta
            rev = item["price"] * qta
            cost_tot = item["cost"] * qta
            st.session_state.sales_history.append({
                "timestamp": datetime.now(), "product_name": item["name"],
                "quantity": qta, "revenue": rev, "cost": cost_tot, "profit": rev - cost_tot
            })
        else:
            st.error(f"Scorte insufficienti per {item['name'] if item else item_id}")
            successo = False
    if successo:
        salva_db_vendite()
        salva_db_inventario()
        st.session_state.carrello = {}
        st.toast("⚡ Transazione Completata", icon="✅")

# --- INTERFACCIA ---

# 1. LOGO (Caricamento e ritaglio automatico per rimuovere spazi)
try:
    img = Image.open("logo.png")
    # Centriamo il logo usando colonne
    _, col_img, _ = st.columns([1, 4, 1])
    with col_img:
        st.image(img, use_container_width=True)
except:
    st.markdown("<h1 style='text-align:center; color:#ff00ff;'>TK LABS</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA"])

# --- TAB 1: CASSA ---
with tab1:
    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("### 🛒 SHOP")
        prodotti = st.session_state.inventory_list
        cols = st.columns(3)
        for i, p in enumerate(prodotti):
            with cols[i % 3]:
                if st.button(f"{p['name']}\n{VALUTA_SIMBOLO}{p['price']:.2f}", key=p['id']):
                    aggiungi_al_carrello(p['id'])
    
    with c2:
        st.markdown("### 🧾 ORDINE")
        totale = 0.0
        for i_id, qta in st.session_state.carrello.items():
            p = next(x for x in prodotti if x['id'] == i_id)
            sub = p['price'] * qta
            totale += sub
            st.write(f"**{qta}x** {p['name']} — {VALUTA_SIMBOLO}{sub:.2f}")
        
        st.divider()
        st.metric("TOTALE", f"{VALUTA_SIMBOLO} {totale:.2f}")
        if st.button("CONFERMA PAGAMENTO", type="primary", use_container_width=True):
            registra_vendita()
            st.rerun()
        if st.button("SVUOTA CARRELLO", use_container_width=True):
            st.session_state.carrello = {}
            st.rerun()

# --- TAB 2: STOCK ---
with tab2:
    st.markdown("### 📦 GESTIONE INVENTARIO")
    df_inv = pd.DataFrame(st.session_state.inventory_list)
    edited_df = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 AGGIORNA DATABASE", type="primary", use_container_width=True):
        st.session_state.inventory_list = edited_df.to_dict('records')
        salva_db_inventario()
        st.success("Dati Salvati")
        st.rerun()
    
    st.divider()
    if st.button("🗑️ RESET TOTALE INVENTARIO"):
        st.session_state.inventory_list = []
        salva_db_inventario()
        st.rerun()

# --- TAB 3: FINANZA ---
with tab3:
    st.markdown("### 💰 RENDIMENTO ATTIVITÀ")
    if st.session_state.sales_history:
        df_s = pd.DataFrame(st.session_state.sales_history)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("INCASSI", f"{VALUTA_SIMBOLO}{df_s['revenue'].sum():.2f}")
        m2.metric("PROFITTO NETTO", f"{VALUTA_SIMBOLO}{df_s['profit'].sum():.2f}")
        m3.metric("MARGINE MEDIO", f"{int((df_s['profit'].sum() / df_s['revenue'].sum()) * 100)}%")
        
        st.divider()
        st.markdown("**REGISTRO TRANSAZIONI**")
        st.dataframe(df_s.sort_index(ascending=False), use_container_width=True, hide_index=True)
        
        st.divider()
        # ESPORTAZIONE
        csv = df_s.to_csv(index=False).encode('utf-8')
        st.download_button("📥 SCARICA REPORT CSV", data=csv, file_name="report_tklz.csv", mime="text/csv", use_container_width=True)
        
        if st.button("💀 AZZERA CRONOLOGIA VENDITE", use_container_width=True):
            st.session_state.sales_history = []
            salva_db_vendite()
            st.rerun()
    else:
        st.info("Nessuna vendita registrata.")
