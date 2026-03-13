import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
import json
import os
from PIL import Image

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="TKLZ | UNDERGROUND ",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TEMA CYBER-PUNK & NEON (CSS AGGIORNATO PER LEGGIBILITÀ) ---
st.markdown("""
    <style>
    /* Sfondo e Font Generale */
    .stApp {
        background-color: #0a0a0a;
        color: #ffffff !important; /* Scritte generali in bianco */
    }
    
    /* Forza il bianco su tutti i testi principali */
    h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Rimozione spazi vuoti intorno al Logo */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        padding: 0 !important;
        margin: -20px 0 -10px 0 !important;
    }

    /* Pulsanti Prodotto - Testo Bianco e Glow */
    .stButton>button {
        width: 100%;
        height: 110px;
        background: rgba(30, 30, 30, 0.8) !important;
        border: 1px solid #444 !important;
        color: #ffffff !important; /* TESTO BIANCO */
        border-radius: 15px !important;
        font-weight: bold !important;
        font-size: 18px !important;
        transition: all 0.3s ease-in-out !important;
        text-transform: uppercase;
    }
    
    .stButton>button:hover {
        border-color: #ff00ff !important;
        box-shadow: 0 0 20px #ff00ff !important;
        transform: scale(1.02);
        color: #ffffff !important;
    }

    /* Bottone Paga - Testo Bianco su fondo scuro verde */
    div.stButton > button[kind="primary"] {
        background: rgba(48, 209, 88, 0.3) !important;
        border: 2px solid #30d158 !important;
        color: #ffffff !important; /* TESTO BIANCO */
    }
    
    div.stButton > button[kind="primary"]:hover {
        background: #30d158 !important;
        color: #000000 !important; /* Diventa nero solo al passaggio per contrasto */
    }

    /* Metriche e Carrello (Testo sempre visibile) */
    [data-testid="stMetricValue"] {
        color: #00ffbc !important; /* Valore numerico in verde neon */
    }
    [data-testid="stMetricLabel"] {
        color: #ffffff !important; /* Etichetta in bianco */
    }

    /* Sistemazione Tabelle (Data Editor) */
    .stDataEditor div {
        color: #ffffff !important;
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
    if 'inventory_list' not in st.session_state:
        if os.path.exists(DB_INVENTARIO):
            with open(DB_INVENTARIO, "r", encoding="utf-8") as f:
                st.session_state.inventory_list = json.load(f)
        else:
            st.session_state.inventory_list = [
                {"id": "kit-1", "name": "🔥 KIT Leash", "cost": 0.80, "price": 5.0, "initial_qty": 400, "current_qty": 400, "is_bundle": False},
                {"id": "drink-1", "name": "🍺 Birra", "cost": 1.00, "price": 5.0, "initial_qty": 200, "current_qty": 200, "is_bundle": False}
            ]
            salva_db_inventario()

    if 'sales_history' not in st.session_state:
        if os.path.exists(DB_VENDITE):
            with open(DB_VENDITE, "r", encoding="utf-8") as f:
                vendite = json.load(f)
                for v in vendite: v['timestamp'] = datetime.fromisoformat(v['timestamp'])
                st.session_state.sales_history = vendite
        else:
            st.session_state.sales_history = []
            salva_db_vendite()

carica_db()

if 'carrello' not in st.session_state:
    st.session_state.carrello = {}

# --- FUNZIONI OPERATIVE ---
def aggiungi_al_carrello(item_id):
    st.session_state.carrello[item_id] = st.session_state.carrello.get(item_id, 0) + 1

def registra_vendita():
    if not st.session_state.carrello: return
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
    salva_db_vendite()
    salva_db_inventario()
    st.session_state.carrello = {}
    st.toast("⚡ Pagamento Confermato", icon="✅")

# --- INTERFACCIA ---
try:
    img = Image.open("logo.png")
    _, col_img, _ = st.columns([1, 4, 1])
    with col_img:
        st.image(img, use_container_width=True)
except:
    st.markdown("<h1 style='text-align:center; color:#ff00ff;'>TKLZ</h1>", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚡ CASSA", "📦 STOCK", "📈 FINANZA"])

with tab1:
    c1, c2 = st.columns([6, 4])
    with c1:
        st.markdown("### 🛒 SHOP")
        prodotti = st.session_state.inventory_list
        for i in range(0, len(prodotti), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(prodotti):
                    p = prodotti[i + j]
                    with cols[j]:
                        if st.button(f"{p['name']}\n{VALUTA_SIMBOLO}{p['price']:.2f}", key=f"btn_{p['id']}"):
                            aggiungi_al_carrello(p['id'])
                            st.rerun()
    
    with c2:
        st.markdown("### 🧾 ORDINE")
        totale = 0.0
        if st.session_state.carrello:
            for i_id, qta in st.session_state.carrello.items():
                p = next((x for x in prodotti if x['id'] == i_id), None)
                if p:
                    sub = p['price'] * qta
                    totale += sub
                    st.write(f"**{qta}x** {p['name']} — **{VALUTA_SIMBOLO}{sub:.2f}**")
            
            st.divider()
            st.metric("TOTALE DA INCASSARE", f"{VALUTA_SIMBOLO} {totale:.2f}")
            if st.button("✅ CONFERMA PAGAMENTO", type="primary", use_container_width=True):
                registra_vendita()
                st.rerun()
            if st.button("🗑️ SVUOTA", use_container_width=True):
                st.session_state.carrello = {}
                st.rerun()
        else:
            st.info("Carrello vuoto")

with tab2:
    st.markdown("### 📦 GESTIONE INVENTARIO")
    df_inv = pd.DataFrame(st.session_state.inventory_list)
    edited_df = st.data_editor(df_inv, num_rows="dynamic", use_container_width=True, hide_index=True)
    
    if st.button("💾 SALVA MODIFICHE STOCK", type="primary", use_container_width=True):
        st.session_state.inventory_list = edited_df.to_dict('records')
        salva_db_inventario()
        st.success("Database aggiornato correttamente.")
        st.rerun()

with tab3:
    st.markdown("### 📈 RENDIMENTO FINANZIARIO")
    if st.session_state.sales_history:
        df_s = pd.DataFrame(st.session_state.sales_history)
        
        # Metriche principali
        m1, m2, m3 = st.columns(3)
        m1.metric("RICAVO TOTALE", f"{VALUTA_SIMBOLO}{df_s['revenue'].sum():.2f}")
        m2.metric("PROFITTO NETTO", f"{VALUTA_SIMBOLO}{df_s['profit'].sum():.2f}")
        m3.metric("MARGINE %", f"{int((df_s['profit'].sum() / df_s['revenue'].sum()) * 100) if df_s['revenue'].sum() > 0 else 0}%")
        
        st.divider()
        st.markdown("**REGISTRO TRANSAZIONI**")
        st.dataframe(df_s.sort_index(ascending=False), use_container_width=True, hide_index=True)
        
        st.divider()
        
        # --- SEZIONE CHIUSURA E RESET ---
        st.markdown("#### 📥 OPERAZIONI DI CHIUSURA")
        
        # Pulsante Esporta Report
        csv = df_s.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 1. SCARICA REPORT VENDITE (CSV)",
            data=csv,
            file_name=f"report_tklz_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
            type="primary" # Mantiene il colore verde neon per l'azione principale
        )
        
        # Spazio minimo tra i pulsanti
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        
        # Pulsante Reset Statistiche
        if st.button("💀 2. AZZERA TUTTE LE STATISTICHE", use_container_width=True):
            st.session_state.sales_history = []
            salva_db_vendite()
            st.toast("Cronologia vendite eliminata", icon="🗑️")
            st.rerun()
            
    else:
        st.info("Ancora nessuna vendita registrata stasera. Il report sarà disponibile dopo la prima transazione.")
