import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Rave Manager | Terminal",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="collapsed" # Chiusa di default per un look più pulito
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
        font-size: 22px !important;
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
        border-color: #00ffcc; /* Neon Cyan */
        color: #00ffcc;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.4);
    }
    
    /* Bottoni specifici (Colori Neon) */
    div.stButton > button[data-testid*="kit"] { border-bottom: 3px solid #ff0055; } /* Neon Pink */
    div.stButton > button[data-testid*="ventaglio"] { border-bottom: 3px solid #0055ff; } /* Neon Blue */
    div.stButton > button[data-testid*="tappi"] { border-bottom: 3px solid #ffaa00; } /* Neon Orange */
    div.stButton > button[data-testid*="bundle"] { border-bottom: 3px solid #00ff00; } /* Neon Green */

    /* Metriche e Tabelle */
    div[data-testid="metric-container"] {
        background-color: #161618;
        border-left: 3px solid #bfff00; /* Lime */
        padding: 15px;
        border-radius: 5px;
    }
    .stDataFrame { border-radius: 5px; }
    
    /* Nascondi header di default di Streamlit per un look più pulito */
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- COSTANTI E CONFIGURAZIONI ---
VALUTA_SIMBOLO = "€"

# --- INIZIALIZZAZIONE DATI ---
if 'inventory_list' not in st.session_state:
    st.session_state.inventory_list = [
        {"id": "kit-1", "name": "🔥 KIT Leash+Acc", "cost": 0.80, "price": 5.0, "initial_qty": 400, "current_qty": 400, "is_bundle": False},
        {"id": "vent-1", "name": "🌬️ Ventaglio", "cost": 0.80, "price": 5.0, "initial_qty": 150, "current_qty": 150, "is_bundle": False},
        {"id": "tapp-1", "name": "👂 Tappi Orecchie", "cost": 0.05, "price": 1.0, "initial_qty": 1000, "current_qty": 1000, "is_bundle": False},
        {"id": "glow-1", "name": "✨ Glow Stick", "cost": 0.10, "price": 1.0, "initial_qty": 500, "current_qty": 500, "is_bundle": False},
        {
            "id": "bundle-starter", "name": "☢️ RAVE PACK", "cost": 1.00, "price": 10.0, 
            "initial_qty": 999, "current_qty": 999, "is_bundle": True, 
            "bundle_composition": {"kit-1": 1, "vent-1": 1, "glow-1": 2}
        }
    ]

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

# --- LOGICA DI VENDITA ---
def registra_vendita(item_id, quantity=1):
    item = next((i for i in st.session_state.inventory_list if i["id"] == item_id), None)
    if not item: return False

    if item.get("is_bundle"):
        comp = item.get("bundle_composition", {})
        # Check stock for all components
        for c_id, c_qty in comp.items():
            c_item = next((i for i in st.session_state.inventory_list if i["id"] == c_id), None)
            if not c_item or c_item["current_qty"] < (c_qty * quantity):
                st.error(f"❌ Stock insufficiente per il componente del bundle!")
                return False
        
        # Deduct stock and calculate cost
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

    # Registra
    st.session_state.sales_history.append({
        "timestamp": datetime.now(),
        "product_name": item["name"],
        "quantity": quantity,
        "revenue": revenue,
        "cost": total_cost,
        "profit": revenue - total_cost
    })
    st.toast(f"✅ VENDUTO: {item['name']}", icon="⚡")
    return True

# --- SIDEBAR (Opzioni Terminale) ---
with st.sidebar:
    st.markdown("### 🎛️ SYS.CTRL")
    if st.button("💀 WIPE SALES DATA"):
        st.session_state.sales_history = []
        st.rerun()
    if st.button("🔄 FACTORY RESET"):
        del st.session_state.inventory_list
        del st.session_state.sales_history
        st.rerun()

# --- MAIN UI ---
st.markdown("## 🦇 RAVE.SYS // POS TERMINAL")

tab_cassa, tab_inventario, tab_analisi = st.tabs(["[1] TERMINALE CASSA", "[2] DB INVENTARIO", "[3] DATI & ANALISI"])

# ==========================================
# TAB 1: CASSA (Minimal POS)
# ==========================================
with tab_cassa:
    st.markdown("#### > READY FOR TRANSACTIONS_")
    
    # Prodotti Singoli
    cols = st.columns(4)
    single_items = [i for i in st.session_state.inventory_list if not i.get("is_bundle")]
    
    for i, item in enumerate(single_items):
        with cols[i % 4]:
            label = f"{item['name']}\n{VALUTA_SIMBOLO}{item['price']:.2f}"
            if st.button(label, key=f"sell_{item['id']}"):
                registra_vendita(item['id'])
                st.rerun()
            st.progress(item["current_qty"] / max(item["initial_qty"], 1), text=f"QTY: {item['current_qty']}")

    st.divider()
    
    # Bundle
    st.markdown("#### > SPECIAL OPS_")
    bundles = [i for i in st.session_state.inventory_list if i.get("is_bundle")]
    b_cols = st.columns(len(bundles) if bundles else 1)
    
    for i, bundle in enumerate(bundles):
        with b_cols[i]:
            label = f"{bundle['name']}\n{VALUTA_SIMBOLO}{bundle['price']:.2f}"
            if st.button(label, key=f"sell_{bundle['id']}"):
                registra_vendita(bundle['id'])
                st.rerun()

# ==========================================
# TAB 2: INVENTARIO
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
    
    # Logica di salvataggio semplificata
    if st.button("💾 SALVA MODIFICHE AL DATABASE"):
        st.session_state.inventory_list = edited_df.to_dict('records')
        st.success("Database aggiornato.")
        st.rerun()

# ==========================================
# TAB 3: ANALISI
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
            # Grafico ad area per i profitti (Underground style)
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
            st.dataframe(df_sales[['timestamp', 'product_name', 'revenue']].tail(8).sort_index(ascending=False), use_container_width=True, hide_index=True)
            
    else:
        st.code("NO_DATA_FOUND // INIZIARE LE VENDITE PER GENERARE LE METRICHE.", language="bash")
