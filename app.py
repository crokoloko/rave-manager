import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt
import json
import os

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="TKLZ | POS Terminal",
    page_icon="🦇",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- TEMA CLEAN & MINIMAL (CSS) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #121212;
        color: #f5f5f7;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
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
    
    .stButton>button:hover {
        transform: translateY(-2px);
        background-color: #2a2a2a;
        border-color: #555555;
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }

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

    div[data-testid="metric-container"] {
        background-color: #1e1e1e;
        border: 1px solid #2d2d2d;
        padding: 15px;
        border-radius: 12px;
    }
    
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- COSTANTI E DATABASE ---
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
            {"id": "drink-1", "name": "🍺 Birra", "cost": 1.00, "price": 5.0, "initial_qty": 200, "current_qty": 200, "is_bundle": False},
            {"id": "kit-1", "name": "🔥 KIT Leash", "cost": 0.80, "price": 5.0, "initial_qty": 400, "current_qty": 400, "is_bundle": False},
            {"id": "vent-1", "name": "🌬️ Ventaglio", "cost": 0.80, "price": 5.0, "initial_qty": 150, "current_qty": 150, "is_bundle": False},
            {"id": "bundle-starter", "name": "☢️ RAVE PACK", "cost": 0.0, "price": 10.0, "initial_qty": 999, "current_qty": 999, "is_bundle": True, "bundle_composition": {"kit-1": 1, "vent-1": 1}}
        ]
        salva_db_inventario()

    if os.path.exists(DB_VENDITE):
        with open(DB_VENDITE, "r", encoding="utf-8") as f:
            vendite = json.load(f)
            for v in vendite:
                v['timestamp'] = datetime.fromisoformat(v['timestamp'])
            st.session_state.sales_history = vendite
    else:
        st.session_state.sales_history = []
        salva_db_vendite()

if 'db_caricato' not in st.session_state:
    carica_db()
    st.session_state.db_caricato = True

if 'carrello' not in st.session_state:
    st.session_state.carrello = {}

# --- FUNZIONI CARRELLO E VENDITA ---
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

    st.session_state.sales_history.append({
        "timestamp": datetime.now(),
        "product_name": item["name"],
        "quantity": quantity,
        "revenue": revenue,
        "cost": total_cost,
        "profit": revenue - total_cost
    })
    
    salva_db_vendite()
    salva_db_inventario()
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

# --- SIDEBAR IMPOSTAZIONI ---
with st.sidebar:
    st.markdown("### 🎛️ IMPOSTAZIONI")
    if st.button("💀 CANCELLA STORICO VENDITE"):
        st.session_state.sales_history = []
        salva_db_vendite()
        st.success("Storico vendite azzerato.")
        st.rerun()
        
    if st.button("🔄 FACTORY RESET DATI"):
        st.session_state.carrello = {}
        if os.path.exists(DB_INVENTARIO): os.remove(DB_INVENTARIO)
        if os.path.exists(DB_VENDITE): os.remove(DB_VENDITE)
        del st.session_state.db_caricato
        st.rerun()

# --- MAIN UI ---
st.markdown("""
    <h2 style='text-align: center; color: #ff00ff; text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff, 0 0 30px #ff00ff; margin-bottom: 20px;'>
        🦇 TKLZ
    </h2>
""", unsafe_allow_html=True)

tab_cassa, tab_inventario, tab_analisi = st.tabs(["[1] TERMINALE CASSA", "[2] DB INVENTARIO", "[3] DATI & ANALISI"])

# ==========================================
# TAB 1: CASSA (Layout a 2 Zone)
# ==========================================
with tab_cassa:
    col_pos, col_receipt = st.columns([6, 4], gap="large")

    with col_pos:
        st.markdown("#### 🛒 TERMINALE OPERATIVO")
        st.markdown("<br>", unsafe_allow_html=True)
        
        prodotti_singoli = [p for p in st.session_state.inventory_list if not p.get("is_bundle")]
        prodotti_bundle = [p for p in st.session_state.inventory_list if p.get("is_bundle")]
        
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
# TAB 2: INVENTARIO (Anti-Doppioni)
# ==========================================
with tab_inventario:
    col_titolo, col_azioni = st.columns([7, 3])
    
    with col_titolo:
        st.markdown("#### > GESTIONE DATABASE")
        
    with col_azioni:
        if st.button("🗑️ AZZERA TUTTO L'INVENTARIO"):
            st.session_state.inventory_list = []
            salva_db_inventario()
            st.rerun()

    st.info("💡 Usa il tasto ➕ nell'angolo in basso a destra della tabella per aggiungere nuovi prodotti da zero.")

    colonne_db = ["id", "name", "cost", "price", "initial_qty", "current_qty", "is_bundle", "bundle_composition"]
    
    if st.session_state.inventory_list:
        df_inv = pd.DataFrame(st.session_state.inventory_list)
    else:
        df_inv = pd.DataFrame(columns=colonne_db)
    
    cfg = {
        "id": st.column_config.TextColumn("ID (Univoco)", required=True, default="nuovo-id"),
        "name": st.column_config.TextColumn("NOME PRODOTTO", required=True, default="Nuovo Prodotto"),
        "cost": st.column_config.NumberColumn("COSTO", format=f"{VALUTA_SIMBOLO}%.2f", default=0.0),
        "price": st.column_config.NumberColumn("PREZZO", format=f"{VALUTA_SIMBOLO}%.2f", default=5.0),
        "initial_qty": st.column_config.NumberColumn("QTA INIZIALE", default=100),
        "current_qty": st.column_config.NumberColumn("QTA ATTUALE", default=100),
        "is_bundle": st.column_config.CheckboxColumn("BUNDLE?", default=False),
        "bundle_composition": st.column_config.TextColumn("COMPOSIZIONE (ID:QTY)")
    }
    
    edited_df = st.data_editor(
        df_inv, 
        key="inv_editor", 
        num_rows="dynamic", 
        column_config=cfg, 
        use_container_width=True, 
        hide_index=True
    )
    
    if st.button("💾 SALVA E AGGIORNA CASSA", type="primary"):
        nuovi_dati = edited_df.to_dict('records')
        lista_id = [item['id'] for item in nuovi_dati if item['id']]
        
        # Controllo di sicurezza per evitare errori critici di Streamlit
        if len(lista_id) != len(set(lista_id)):
            st.error("❌ ERRORE: Hai inserito due o più prodotti con lo STESSO ID! Modifica la prima colonna in modo che ogni ID sia diverso (es. kit-1, kit-2).")
        else:
            st.session_state.inventory_list = nuovi_dati
            salva_db_inventario()
            st.success("Database aggiornato! La cassa ora riflette i nuovi prodotti.")
            st.rerun()

# ==========================================
# TAB 3: ANALISI E REPORT (Con Esportazione CSV)
# ==========================================
with tab_analisi:
    col_titolo_an, col_export = st.columns([7, 3])
    
    with col_titolo_an:
        st.markdown("#### > METRICHE DI SISTEMA")
        
    with col_export:
        if st.session_state.sales_history:
            df_export = pd.DataFrame(st.session_state.sales_history)
            csv_data = df_export.to_csv(index=False).encode('utf-8')
            nome_file = f"chiusura_cassa_{datetime.now().strftime('%Y_%m_%d')}.csv"
            
            st.download_button(
                label="📥 ESPORTA REPORT (CSV)",
                data=csv_data,
                file_name=nome_file,
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

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
