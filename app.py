import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Rave Manager | Terminal",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TEMA DARK/UNDERGROUND (CSS) ---
st.markdown("""
    <style>
    /* Sfondo generale e font */
    .stApp {
        background-color: #0a0a0a;
        color: #e0e0e0;
    }
    
    /* Stile Bottoni Cassa - Vibe Neon/Terminale */
    .stButton>button {
        width: 100%;
        height: 100px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 20px !important;
        font-weight: bold;
        border-radius: 8px;
        background-color: #111111;
        border: 1px solid #333333;
        color: #ffffff;
        transition: all 0.3s ease;
        box-shadow: 0 0 5px rgba(0, 0, 0, 0.5);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        border-color: #00ffcc;
        color: #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.4);
    }
    
    /* Colori Neon specifici per i pulsanti */
    div.stButton > button[data-testid*="kit"] { border-bottom: 3px solid #ff0055; }
    div.stButton > button[data-testid*="vent"] { border-bottom: 3px solid #0055ff; }
    div.stButton > button[data-testid*="tapp"] { border-bottom: 3px solid #ffaa00; }
    div.stButton > button[data-testid*="glow"] { border-bottom: 3px solid #cc00ff; }
    div.stButton > button[data-testid*="bundle"] { border-bottom: 3px solid #00ff00; }

    /* Bottone Paga (Primary) */
    div.stButton > button[kind="primary"] {
        background-color: #00ffcc;
        color: #000000;
        border: none;
        border-bottom: 3px solid #00b38f;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #33ffdb;
        color: #000000;
    }

    /* Metriche e Tabelle */
    div[data-testid="metric-container"] {
        background-color: #161618;
        border-left: 3px solid #bfff00;
        padding: 15px;
        border-radius: 5px;
    }
    
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
    st.markdown("### 🎛️ SYS.CTRL")
    if st.button("💀 WIPE SALES DATA"):
        st.session_state.sales_history = []
        st.rerun()
    if st.button("🔄 FACTORY RESET"):
        st.session_state.carrello = {}
        del st.session_state.inventory_list
        del st.session_state.sales_history
        st.rerun()

# --- MAIN UI ---
st.markdown("## 🦇 RAVE.SYS // POS TERMINAL")

tab_cassa, tab_inventario, tab_analisi = st.tabs(["[1] TERMINALE CASSA", "[2] DB INVENTARIO", "[3] DATI & ANALISI"])

# ==========================================
# TAB 1: CASSA (Layout a 2 Zone con Carrello)
# ==========================================
with tab_cassa:
    col_pos, col_receipt = st.columns([6, 4], gap="large")

    # --- ZONA SINISTRA: TASTIERA ---
    with col_pos:
        st.markdown("#### 👕 GEAR & MERCH")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.button("🔥 KIT Leash\n€5.00", key="btn_kit", on_click=aggiungi_al_carrello, args=("kit-1",))
        with col_m2: st.button("🌬️ Ventaglio\n€5.00", key="btn_vent", on_click=aggiungi_al_carrello, args=("vent-1",))
        with col_m3: st.button("👂 Tappi\n€1.00", key="btn_tapp", on_click=aggiungi_al_carrello, args=("tapp-1",))

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### ⚡ ENERGY & GLOW")
        col_g1, col_g2 = st.columns(2)
        with col_g1: st.button("✨ Glow Stick\n€1.00", key="btn_glow", on_click=aggiungi_al_carrello, args=("glow-1",))

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("#### 🎁 BUNDLE SPECIALI")
        st.button("☢️ RAVE PACK (Kit+Vent+2Glow)\n€10.00", key="btn_bundle", on_click=aggiungi_al_carrello, args=("bundle-starter",))

    # --- ZONA DESTRA: SCONTRINO/CARRELLO ---
    with col_receipt:
        st.markdown("""
            <div style='background-color: #1a1a1c; padding: 20px; border-radius: 10px; border: 1px solid #333;'>
                <h3 style='margin-top: 0; color: #00ffcc;'>🛒 ORDINE ATTUALE</h3>
        """, unsafe_allow_html=True)
        
        totale_ordine = 0.0
        
        if st.session_state.carrello:
            for item_id, qta in st.session_state.carrello.items():
                item_info = next((i for i in st.session_state.inventory_list if i["id"] == item_id), None)
                if item_info:
                    subtotale = item_info["price"] * qta
                    totale_ordine += subtotale
                    st.markdown(f"**{qta}x** {item_info['name']} = **€{subtotale:.2f}**")
            
            st.divider()
            st.metric(label="TOTALE DA INCASSARE", value=f"€ {totale_ordine:.2f}")
            st.markdown("<br>", unsafe_allow_html=True)
            
            col_btn_1, col_btn_2 = st.columns(2)
            with col_btn_1:
                st.button("❌ ANNULLA", use_container_width=True, on_click=svuota_carrello)
            with col_btn_2:
                st.button("✅ PAGA", type="primary", use_container_width=True, on_click=conferma_ordine)
                
        else:
            st.info("Terminale pronto. Aggiungi prodotti all'ordine.")
            st.metric(label="TOTALE DA INCASSARE", value="€ 0.00")
            
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 2: INVENTARIO (CRUD)
# ==========================================
with tab_inventario:
    st.markdown("#### > DATABASE MANAGEMENT_")
    df_inv = pd.DataFrame(st.session_state.inventory_list)
    
    cfg = {
        "id": st.column_config.TextColumn("ID", disabled=True),
        "name": st.column_config.TextColumn("NOME"),
        "cost": st.column_config.NumberColumn("COSTO", format="€%.2f"),
        "price": st.column_config.NumberColumn("PREZZO", format="€%.2f"),
        "initial_qty": st.column_config.NumberColumn("QTA INIZIALE"),
        "current_qty": st.column_config.NumberColumn("QTA ATTUALE", disabled=True),
        "is_bundle": st.column_config.CheckboxColumn("BUNDLE?"),
        "bundle_composition": st.column_config.TextColumn("COMPOSIZIONE (ID:QTY)")
    }
    
    edited_df = st.data_editor(df_inv, key="inv_editor", num_rows="dynamic", column_config=cfg, use_container_width=True, hide_index=True)
    
    if st.button("💾 SALVA MODIFICHE AL DATABASE"):
        st.session_state.inventory_list = edited_df.to_dict('records')
        st.success("Database aggiornato.")
        st.rerun()

# ==========================================
# TAB 3: ANALISI E REPORT
# ==========================================
with tab_analisi:
    st.markdown("#### > SYSTEM METRICS_")
    
    if st.session_state.sales_history:
        df_sales = pd.DataFrame(st.session_state.sales_history)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("REVENUE", f"{VALUTA_SIMBOLO}{df_sales['revenue'].sum():.2f}")
        m2.metric("COSTS", f"{VALUTA_SIMBOLO}{df_sales['cost'].sum():.2f}")
        m3.metric("NET PROFIT", f"{VALUTA_SIMBOLO}{df_sales['profit'].sum():.2f}")
        m4.metric("UNITS SOLD", f"{df_sales['quantity'].sum()}")
        
        st.divider()
        
        c1, c2 = st.columns([2, 1])
        with c1:
            df_sales['cumulative'] = df_sales['profit'].cumsum()
            chart = alt.Chart(df_sales).mark_area(
                line={'color':'#00ffcc'}, color=alt.Gradient(
                    gradient='linear', stops=[alt.GradientStop(color='#00ffcc', offset=0), alt.GradientStop(color='#0a0a0a', offset=1)], x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('timestamp:T', title='TIME', axis=alt.Axis(grid=False)),
                y=alt.Y('cumulative:Q', title='PROFIT', axis=alt.Axis(grid=False))
            ).properties(height=300)
            st.altair_chart(chart, use_container_width=True)
            
        with c2:
            st.markdown("**ULTIME VENDITE CONFERMATE**")
            st.dataframe(df_sales[['timestamp', 'product_name', 'revenue']].tail(8).sort_index(ascending=False), use_container_width=True, hide_index=True)
            
    else:
        st.code("NO_DATA_FOUND // NESSUNA TRANSAZIONE REGISTRATA.", language="bash")


