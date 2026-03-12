import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Rave Manager | POS",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TEMA CLEAN & MINIMAL (CSS) ---
st.markdown("""
    <style>
    /* Sfondo generale elegante e meno aggressivo */
    .stApp {
        background-color: #121212;
        color: #f5f5f7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Bottoni Cassa - Clean & Modern */
    .stButton>button {
        width: 100%;
        height: 100px;
        font-size: 20px !important;
        font-weight: 600;
        border-radius: 12px;
        background-color: #1e1e1e;
        border: 1px solid #2d2d2d;
        color: #f5f5f7;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Hover sottile e tattile */
    .stButton>button:hover {
        transform: translateY(-2px);
        background-color: #2a2a2a;
        border-color: #555555;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }

    /* Bottone Paga (Primary) - Verde brillante e pulito */
    div.stButton > button[kind="primary"] {
        background-color: #30d158;
        color: #ffffff;
        border: none;
        box-shadow: 0 4px 10px rgba(48, 209, 88, 0.2);
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #2db34c;
        color: #ffffff;
    }

    /* Metriche e Box laterali */
    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border: 1px solid #2d2d2d;
        padding: 15px;
        border-radius: 12px;
    }
    
    /* Nasconde l'header di default per pulizia */
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- COSTANTI E CONFIGURAZIONI ---
VALUTA_SIMBOLO = "€"

# --- INIZIALIZZAZIONE DATI ---
if 'inventory_list' not in st.session_state:
    st.session_state.inventory_list = [
        {"id": "kit-1", "name": "🔥 KIT Leash", "cost": 0.80, "price": 5.0, "initial_qty": 400, "current_qty": 400, "is_bundle": False},
        {"id": "vent-1", "name": "🌬️ Ventaglio", "cost": 0.80, "price": 5.0, "initial_qty": 150, "current_qty": 150, "is_bundle": False},
        {"id": "tapp-1", "name": "👂 Tappi", "cost": 0.05, "price": 1.0, "initial_qty": 1000, "current_qty": 1000, "is_bundle": False},
        {"id": "glow-1", "name": "✨ Glow Stick", "cost": 0.10, "price": 1.0, "initial_qty": 500, "current_qty": 500, "is_bundle": False},
        {
            "id": "bundle-starter", "name": "☢️ RAVE PACK", "cost": 1.00, "price": 10.0, 
            "initial_qty": 999, "current_qty": 999, "is_bundle": True, 
            "bundle_composition": {"kit-1": 1, "vent-1": 1, "glow-1": 2}
        }
    ]

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

if 'carrello' not in st.session_state:
    st.session_state.carrello = {}

# --- FUNZIONI LOGICHE (CALLBACKS) ---
def aggiungi_al_carrello(item_id):
    if item_id in st.session_state.carrello:
        st.session_state.carrello[item_id] += 1
    else:
        st.session_state.carrello[item_id] = 1

def svuota_carrello():
    st.session_state.carrello = {}

def registra_vendita(item_id, quantity=1):
    item = next((i for i in st.session_state.inventory_list if i["id"] == item_id), None)
    if not item: return False

    if item.get("is_bundle"):
        comp = item.get("bundle_composition", {})
        # Verifica scorte componenti
        for c_id, c_qty in comp.items():
            c_item = next((i for i in st.session_state.inventory_list if i["id"] == c_id), None)
            if not c_item or c_item["current_qty"] < (c_qty * quantity):
                st.error(f"❌ Stock insufficiente per comporre il bundle!")
                return False
        
        total_cost = 0
        for c_id, c_qty in comp.items():
            c_item = next((i for i in st.session_state.inventory_list if i["id"] == c_id))
            c_item["current_qty"] -= (c_qty * quantity)
            total_cost += c_item["cost"] * (c_qty * quantity)
        
        revenue = item["price"] * quantity
    else:
        if item["current_qty"] < quantity:
            st.error(f"❌ ESAURITO: {item['name']}")
            return False
        item["current_qty"] -= quantity
        total_cost = item["cost"] * quantity
        revenue = item["price"] * quantity

    # Registra nel database storico
    st.session_state.sales_history.append({
        "timestamp": datetime.now(),
        "product_name": item["name"],
        "quantity": quantity,
        "revenue": revenue,
        "cost": total_cost,
        "profit": revenue - total_cost
    })
    return True

def conferma_ordine():
    if not st.session_state.carrello:
        return

    successo_totale = True
    for item_id, qta in st.session_state.carrello.items():
        if not registra_vendita(item_id, quantity=qta):
            successo_totale = False
            
    if successo_totale:
        st.toast("✅ PAGAMENTO RICEVUTO! Ordine salvato.", icon="⚡")
    svuota_carrello()

# --- SIDEBAR (SYS.CTRL) ---
with st.sidebar:
    st.markdown("### 🎛️ IMPOSTAZIONI")
    if st.button("💀 CANCELLA STORICO VENDITE"):
        st.session_state.sales_history = []
        st.rerun()
    if st.button("🔄 FACTORY RESET DATI"):
        st.session_state.carrello = {}
        del st.session_state.inventory_list
        del st.session_state.sales_history
        st.rerun()

# --- MAIN UI ---
st.markdown("## 🦇 RAVE // POS TERMINAL")

tab_cassa, tab_inventario, tab_analisi = st.tabs(["[1] TERMINALE CASSA", "[2] DB INVENTARIO", "[3] DATI & ANALISI"])

# ==========================================
# TAB 1: CASSA (Layout a 2 Zone Dinamico)
# ==========================================
with tab_cassa:
    col_pos, col_receipt = st.columns([6, 4], gap="large")

    # --- ZONA SINISTRA: TASTIERA DINAMICA ---
    with col_pos:
        st.markdown("#### 🛒 TERMINALE OPERATIVO")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Filtra i prodotti dall'inventario
        prodotti_singoli = [p for p in st.session_state.inventory_list if not p.get("is_bundle")]
        prodotti_bundle = [p for p in st.session_state.inventory_list if p.get("is_bundle")]
        
        # 1. Generazione Prodotti Singoli
        if prodotti_singoli:
            st.markdown("##### 👕 PRODOTTI")
            colonne_singoli = st.columns(3)
            
            for i, item in enumerate(prodotti_singoli):
                with colonne_singoli[i % 3]:
                    label_bottone = f"{item['name']}\n{VALUTA_SIMBOLO}{item['price']:.2f}"
                    st.button(
                        label_bottone, 
                        key=f"btn_{item['id']}", 
                        on_click=aggiungi_al_carrello, 
                        args=(item["id"],)
                    )

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. Generazione Bundle
        if prodotti_bundle:
            st.markdown("##### 🎁 BUNDLE SPECIALI")
            colonne_bundle = st.columns(2)
            
            for i, item in enumerate(prodotti_bundle):
                with colonne_bundle[i % 2]:
                    label_bottone = f"{item['name']}\n{VALUTA_SIMBOLO}{item['price']:.2f}"
                    st.button(
                        label_bottone, 
                        key=f"btn_{item['id']}", 
                        on_click=aggiungi_al_carrello, 
                        args=(item["id"],)
                    )

    # --- ZONA DESTRA: SCONTRINO/CARRELLO ---
    with col_receipt:
        st.markdown("""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 12px; border: 1px solid #2d2d2d;'>
                <h3 style='margin-top: 0; color: #f5f5f7;'>🛒 ORDINE ATTUALE</h3>
        """, unsafe_allow_html=True)
        
        totale_ordine = 0.0
        
        if st.session_state.carrello:
            for item_id, qta in st.session_state.carrello.items():
                item_info = next((i for i in st.session_state.inventory_list if i["id"] == item_id), None)
                if item_info:
                    subtotale = item_info["price"] * qta
                    totale_ordine += subtotale
                    st.markdown(f"**{qta}x** {item_info['name']} = **{VALUTA_SIMBOLO}{subtotale:.2f}**")
            
            st.divider()
            st.metric(label="TOTALE DA INCASSARE", value=f"{VALUTA_SIMBOLO} {totale_ordine:.2f}")
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_btn_1, col_btn_2 = st.columns(2)
            with col_btn_1:
                st.button("❌ ANNULLA", use_container_width=True, on_click=svuota_carrello)
            with col_btn_2:
                st.button("✅ PAGA", type="primary", use_container_width=True, on_click=conferma_ordine)
                
        else:
            st.info("Terminale pronto. Aggiungi prodotti all'ordine.")
            st.metric(label="TOTALE DA INCASSARE", value=f"{VALUTA_SIMBOLO} 0.00")
            
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 2: INVENTARIO (CRUD COMPLETO)
# ==========================================
with tab_inventario:
    st.markdown("#### > GESTIONE DATABASE")
    df_inv = pd.DataFrame(st.session_state.inventory_list)
    
    # Configurazione sbloccata per permettere modifiche totali
    cfg = {
        "id": st.column_config.TextColumn("ID (Univoco)", required=True),
        "name": st.column_config.TextColumn("NOME PRODOTTO"),
        "cost": st.column_config.NumberColumn("COSTO", format=f"{VALUTA_SIMBOLO}%.2f"),
        "price": st.column_config.NumberColumn("PREZZO", format=f"{VALUTA_SIMBOLO}%.2f"),
        "initial_qty": st.column_config.NumberColumn("QTA INIZIALE"),
        "current_qty": st.column_config.NumberColumn("QTA ATTUALE"),
        "is_bundle": st.column_config.CheckboxColumn("BUNDLE?"),
        "bundle_composition": st.column_config.TextColumn("COMPOSIZIONE (ID:QTY)")
    }
    
    edited_df = st.data_editor(df_inv, key="inv_editor", num_rows="dynamic", column_config=cfg, use_container_width=True, hide_index=True)
    
    if st.button("💾 SALVA E AGGIORNA CASSA"):
        st.session_state.inventory_list = edited_df.to_dict('records')
        st.success("Database e pulsanti cassa aggiornati con successo!")
        st.rerun()

# ==========================================
# TAB 3: ANALISI E REPORT
# ==========================================
with tab_analisi:
    st.markdown("#### > METRICHE DI SISTEMA")
    
    if st.session_state.sales_history:
        df_sales = pd.DataFrame(st.session_state.sales_history)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("RICAVO", f"{VALUTA_SIMBOLO}{df_sales['revenue'].sum():.2f}")
        m2.metric("COSTI MERCE", f"{VALUTA_SIMBOLO}{df_sales['cost'].sum():.2f}")
        m3.metric("PROFITTO NETTO", f"{VALUTA_SIMBOLO}{df_sales['profit'].sum():.2f}")
        m4.metric("UNITÀ VENDUTE", f"{df_sales['quantity'].sum()}")
        
        st.divider()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            df_sales['cumulative'] = df_sales['profit'].cumsum()
            chart = alt.Chart(df_sales).mark_area(
                line={'color':'#30d158'}, color=alt.Gradient(
                    gradient='linear', stops=[alt.GradientStop(color='#30d158', offset=0), alt.GradientStop(color='#121212', offset=1)], x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('timestamp:T', title='TEMPO', axis=alt.Axis(grid=False)),
                y=alt.Y('cumulative:Q', title='PROFITTO', axis=alt.Axis(grid=False))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
        with c2:
            st.markdown("**ULTIME VENDITE**")
            st.dataframe(df_sales[['timestamp', 'product_name', 'revenue']].tail(8).sort_index(ascending=False), use_container_width=True, hide_index=True)
            
    else:
        st.info("Nessuna transazione registrata. Inizia a vendere per popolare i grafici.")
