import streamlit as st
import pandas as pd
from datetime import datetime
import altair as alt

# --- CONFIGURAZIONE PAGINA E TEMA ---
st.set_page_config(
    page_title="RaveBusiness Manager | Pro Cassa",
    page_icon="🕶️",
    layout="wide", # Usa tutto lo schermo per una visione professionale
    initial_sidebar_state="expanded"
)

# Applica un tema personalizzato con CSS (soprattutto per i pulsanti)
st.markdown("""
    <style>
    /* Stile per i pulsanti di vendita grandi e colorati */
    .stButton>button {
        width: 100%;
        height: 120px; /* Più alti e leggibili */
        font-size: 26px !important;
        font-weight: bold;
        border-radius: 20px;
        margin-bottom: 20px;
        transition: transform 0.2s;
        border: none;
        color: white;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        opacity: 0.9;
    }
    
    /* Colori specifici per i pulsanti */
    div.stButton > button[data-testid*="kit"] { background-color: #ff4b4b; } /* Rosso per i Kit */
    div.stButton > button[data-testid*="ventaglio"] { background-color: #4b86ff; } /* Blu per i Ventagli */
    div.stButton > button[data-testid*="tappi"] { background-color: #ffb84b; } /* Arancio per i Tappi */
    div.stButton > button[data-testid*="bundle"] { background-color: #4bff4b; } /* Verde per i Bundle */

    /* Miglioramenti layout per tabelle e metriche */
    .stMetric { background-color: #2e313a; padding: 15px; border-radius: 10px; border: 1px solid #4a4d55; }
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- COSTANTI E CONFIGURAZIONI ---
VALUTA_SIMBOLO = "€"
COLORE_TESTO = "#fafafa"

# --- INIZIALIZZAZIONE DATI (DATABASE TEMPORANEO IN-SESSION) ---
if 'inventory_list' not in st.session_state:
    # Campione di dati iniziale per il primo lancio
    st.session_state.inventory_list = [
        {"id": "kit-1", "name": "🔥 KIT Leash+Acc", "cost": 0.80, "price": 5.0, "initial_qty": 400, "current_qty": 400},
        {"id": "vent-1", "name": "🌬️ Ventaglio", "cost": 0.80, "price": 5.0, "initial_qty": 150, "current_qty": 150},
        {"id": "tapp-1", "name": "👂 Tappi Orecchie", "cost": 0.05, "price": 1.0, "initial_qty": 1000, "current_qty": 1000},
        {"id": "glow-1", "name": "✨ Glow Stick", "cost": 0.10, "price": 1.0, "initial_qty": 500, "current_qty": 500}
    ]

if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

# --- LOGICA DI VENDITA ---
def registra_vendita(item_id, quantity=1, is_bundle=False, bundle_composition_dict=None):
    """
    Registra una vendita, gestendo la logica di stock e bundle.
    Ritorna True se la vendita ha successo, False altrimenti.
    """
    # Trova l'articolo principale
    main_item = next((item for item in st.session_state.inventory_list if item["id"] == item_id), None)
    
    if is_bundle:
        # Gestione bundle: verifica disponibilità di TUTTI gli articoli
        if not bundle_composition_dict or not isinstance(bundle_composition_dict, dict):
            st.error("Errore: Composizione bundle non valida.")
            return False
            
        # Verifica stock
        for comp_item_id, comp_qty in bundle_composition_dict.items():
            comp_item = next((item for item in st.session_state.inventory_list if item["id"] == comp_item_id), None)
            if not comp_item or comp_item["current_qty"] < comp_qty * quantity:
                st.error(f"❌ Errore Bundle: Stock insufficiente per {comp_item['name'] if comp_item else comp_item_id}!")
                return False
                
        # Esegui vendita bundle
        total_revenue = main_item["price"] * quantity
        total_cost = 0
        
        for comp_item_id, comp_qty in bundle_composition_dict.items():
            comp_item = next((item for item in st.session_state.inventory_list if item["id"] == comp_item_id), None)
            comp_item["current_qty"] -= comp_qty * quantity
            total_cost += comp_item["cost"] * comp_qty * quantity
            
        main_item["current_qty"] -= 1 # Sottrae 1 per il bundle stesso se è tracciato, opzionale
        
        vendita = {
            "timestamp": datetime.now(),
            "product_name": main_item["name"],
            "item_id": item_id,
            "quantity": quantity,
            "revenue": total_revenue,
            "cost": total_cost,
            "profit": total_revenue - total_cost
        }
        st.session_state.sales_history.append(vendita)
        st.toast(f"💰 BUNDLE VENDUTO: {main_item['name']}! ✅", icon="💰")
        return True
        
    else:
        # Gestione articolo singolo
        if main_item["current_qty"] >= quantity:
            main_item["current_qty"] -= quantity
            revenue = main_item["price"] * quantity
            cost = main_item["cost"] * quantity
            vendita = {
                "timestamp": datetime.now(),
                "product_name": main_item["name"],
                "item_id": item_id,
                "quantity": quantity,
                "revenue": revenue,
                "cost": cost,
                "profit": revenue - cost
            }
            st.session_state.sales_history.append(vendita)
            st.toast(f"✅ Venduto: {main_item['name']} x{quantity}!", icon="🎉")
            return True
        else:
            st.error(f"❌ ESAURITO: {main_item['name']}! Scorta attuale: {main_item['current_qty']}", icon="❌")
            return False

# --- UI BARRA LATERALE ---
with st.sidebar:
    st.title("🛡️ Rave Manager Pro")
    st.write(f"Gestione Vendite per Eventi")
    st.divider()
    
    # Sezione Impostazioni
    st.header("⚙️ Impostazioni App")
    formato_valuta = st.selectbox("Simbolo Valuta", [f"{VALUTA_SIMBOLO} (Euro)", f"$ (Dollaro)", f"£ (Sterlina)"])
    VALUTA_SIMBOLO = formato_valuta.split(" ")[0]
    
    st.divider()
    
    # Sezione Azioni
    st.header("🛠️ Azioni Dati")
    st.caption("🚨 ATTENZIONE: Il reset cancella TUTTE le vendite della sessione.")
    col_reset, col_clear = st.columns(2)
    with col_reset:
        if st.button("Restor. Default"):
            # Cancella vendite e ripristina inventario di esempio
            del st.session_state.inventory_list
            del st.session_state.sales_history
            st.rerun()
    with col_clear:
        if st.button("Cancella Vendite"):
            st.session_state.sales_history = []
            st.rerun()
            
    st.divider()
    st.caption(f"Powered by Streamlit | v1.0 Pro")

# --- UI MAIN AREA ---
tab_cassa, tab_inventario, tab_analisi = st.tabs(["💸 CASSA VELOCE", "📦 INVENTARIO (CRUD)", "📈 ANALISI & REPORT"])

# ==========================================================
# TAB 1: CASSA VELOCE (Vendita rapida)
# ==========================================================
with tab_cassa:
    st.header("💸 Punto Cassa Rapido")
    st.write("Tocca i pulsanti per registrare le vendite al volo.")
    st.divider()
    
    # Layout a colonne per i prodotti
    num_colonne = 3
    colonne = st.columns(num_colonne)
    
    # Genera dinamicamente i pulsanti per ogni articolo non-bundle
    for i, item in enumerate(st.session_state.inventory_list):
        if not item.get("is_bundle", False): # Evita i bundle qui, per ora
            col_idx = i % num_colonne
            with colonne[col_idx]:
                label_pulsante = f"{item['name']}\n{VALUTA_SIMBOLO} {item['price']:.2f}"
                pulsante_key = f"sell_{item['id']}" # Chiave unica per Streamlit
                
                if st.button(label_pulsante, key=pulsante_key):
                    registra_vendita(item["id"], 1)
                    st.rerun() # Ricarica per aggiornare stock nell'interfaccia
                
                # Sotto il pulsante, mostra lo stock rimanente con una barra di progresso
                stock_percent = max(0, min(100, item["current_qty"] / item["initial_qty"] * 100)) if item["initial_qty"] > 0 else 0
                st.progress(stock_percent / 100, text=f"Stock: {item['current_qty']} pz")
    
    st.divider()
    
    # Sezione Speciale: Bundle
    st.subheader("🎁 Offerte Bundle Speciali")
    
    # Definisci il bundle "Starter Pack" di esempio, se non già esistente nell'inventario
    if not next((item for item in st.session_state.inventory_list if item["id"] == "bundle-starter"), None):
        bundle_item = {
            "id": "bundle-starter", 
            "name": "🎁 Rave Starter Pack", 
            "cost": 0.0, # Calcolato dinamicamente al momento della vendita
            "price": 10.0, 
            "initial_qty": 0, # Non tracciato separatamente
            "current_qty": 0, 
            "is_bundle": True,
            "bundle_composition": {"kit-1": 1, "vent-1": 1, "glow-1": 2} # ID: Qty
        }
        st.session_state.inventory_list.append(bundle_item)
        
    starter_bundle = next((item for item in st.session_state.inventory_list if item["id"] == "bundle-starter"), None)
    
    label_bundle = f"{starter_bundle['name']}\n{VALUTA_SIMBOLO} {starter_bundle['price']:.2f}\n(Kit + Ventaglio + 2 Glow)"
    if st.button(label_bundle, key="sell_bundle_starter", help="Include 1 Kit, 1 Ventaglio, 2 Glow Stick"):
        # Recupera la composizione
        composition_dict = starter_bundle.get("bundle_composition", {})
        registra_vendita("bundle-starter", 1, is_bundle=True, bundle_composition_dict=composition_dict)
        st.rerun()

# ==========================================================
# TAB 2: GESTIONE INVENTARIO (CRUD Professionale)
# ==========================================================
with tab_inventario:
    st.header("📦 Gestione Inventario")
    st.write("Modifica, aggiungi e rimuovi prodotti a piacimento usando la tabella interattiva.")
    st.write("**⚠️ NOTA BENE:** Le modifiche sono temporanee e si cancelleranno se ricarichi la pagina o chiudi l'app.")
    st.divider()
    
    # Converte la lista in DataFrame per st.data_editor
    inventory_df = pd.DataFrame(st.session_state.inventory_list)
    
    # Configurazione colonne per renderle carine e funzionali
    configurazione_colonne = {
        "id": st.column_config.TextColumn("ID Prodotto", help="Chiave univoca, non modificabile per articoli esistenti", disabled=True),
        "name": st.column_config.TextColumn("Nome Prodotto", help="Nome descrittivo con icone"),
        "cost": st.column_config.NumberColumn(f"Costo Unitario ({VALUTA_SIMBOLO})", format=f"{VALUTA_SIMBOLO} %.2f", min_value=0.0),
        "price": st.column_config.NumberColumn(f"Prezzo Vendita ({VALUTA_SIMBOLO})", format=f"{VALUTA_SIMBOLO} %.2f", min_value=0.0),
        "initial_qty": st.column_config.NumberColumn("Qta Iniziale (Carico)", min_value=1, step=1),
        "current_qty": st.column_config.NumberColumn("Qta Attuale", min_value=0, step=1, disabled=True, help="Scorta rimanente in tempo reale"),
        "is_bundle": st.column_config.CheckboxColumn("È un Bundle?", help="Imposta a True se è un pacchetto composto da altri articoli"),
        "bundle_composition": st.column_config.TextColumn("Composizione Bundle", help="Se bundle, scrivi ID:Qtà separati da virgola. Esempio: kit-1:1, vent-1:1", disabled=True)
    }
    
    # Interfaccia CRUD: Data Editor Interattivo
    st.subheader("📋 Tabella Inventario Completa")
    
    edited_inventory_df = st.data_editor(
        inventory_df, 
        key="inventory_editor", 
        num_rows="dynamic", # Permette di aggiungere e rimuovere righe
        column_config=configurazione_colonne,
        use_container_width=True,
        hide_index=True
    )
    
    # Gestione modifiche: Aggiorna lo stato della sessione basato sulle modifiche nel data editor
    if st.session_state.get("inventory_editor", {}).get("edited_rows"):
        # Itera sulle righe modificate e aggiorna la lista
        for row_index, changes in st.session_state.inventory_editor["edited_rows"].items():
            current_item_id = edited_inventory_df.iloc[row_index]["id"]
            # Trova l'articolo corrispondente nella lista e aggiornalo
            for i, item in enumerate(st.session_state.inventory_list):
                if item["id"] == current_item_id:
                    # Aggiorna i campi modificati
                    st.session_state.inventory_list[i].update(changes)
                    # Gestione speciale: se Qta Iniziale cambia, aggiorna anche Qta Attuale per articoli nuovi/con stock pieno
                    if "initial_qty" in changes and item["initial_qty"] == item["current_qty"]:
                         st.session_state.inventory_list[i]["current_qty"] = changes["initial_qty"]
                    break
        st.rerun() # Forza il ricaricamento per mostrare le modifiche altrove
        
    elif st.session_state.get("inventory_editor", {}).get("added_rows"):
        # Gestione aggiunta nuovi prodotti: Genera un ID e assicurati che i dati siano corretti
        for changes in st.session_state.inventory_editor["added_rows"]:
            # Genera un ID unico e semplice, se non fornito
            new_id = f"item-{len(st.session_state.inventory_list) + 1}"
            
            # Crea il nuovo articolo con valori di default se non forniti
            new_item = {
                "id": new_id,
                "name": changes.get("name", f"Nuovo Prodotto {len(st.session_state.inventory_list) + 1}"),
                "cost": changes.get("cost", 0.0),
                "price": changes.get("price", 10.0),
                "initial_qty": changes.get("initial_qty", 100),
                "current_qty": changes.get("initial_qty", 100),
                "is_bundle": changes.get("is_bundle", False),
                "bundle_composition": changes.get("bundle_composition", "")
            }
            st.session_state.inventory_list.append(new_item)
        st.rerun()

    elif st.session_state.get("inventory_editor", {}).get("deleted_rows"):
        # Gestione rimozione prodotti
        indices_to_delete = sorted(st.session_state.inventory_editor["deleted_rows"], reverse=True)
        for row_index in indices_to_delete:
            item_to_delete_id = edited_inventory_df.iloc[row_index]["id"]
            st.session_state.inventory_list = [item for item in st.session_state.inventory_list if item["id"] != item_to_delete_id]
        st.rerun()

    st.divider()
    
    # Guida Rapida CRUD
    with st.expander("ℹ️ Guida Rapida Modifica Inventario"):
        st.markdown("""
        **Come funziona la tabella di gestione:**
        - **Modificare:** Fai doppio clic su una cella per cambiarne il valore. I campi *ID* e *Qta Attuale* sono disabilitati.
        - **Aggiungere:** Clicca sul pulsante **"+"** in alto a destra della tabella per creare una nuova riga. Compila i campi.
        - **Rimuovere:** Seleziona una o più righe cliccando sulla casella a sinistra, quindi premi il tasto **"Canc"** sulla tastiera o l'icona del cestino che appare in alto a destra della tabella.
        - **Qta Iniziale vs Attuale:** La *Qta Iniziale* è il carico totale che hai effettuato. La *Qta Attuale* è quella calcolata dopo le vendite e non può essere modificata manualmente. Per reset, usa i pulsanti nella barra laterale.
        """)

# ==========================================================
# TAB 3: ANALISI E REPORT (Visualizzazione Professionale)
# ==========================================================
with tab_analisi:
    st.header("📈 Analisi Vendite e Profitti")
    st.divider()
    
    if st.session_state.sales_history:
        # Converti cronologia vendite in DataFrame per analisi
        sales_df = pd.DataFrame(st.session_state.sales_history)
        sales_df['timestamp'] = pd.to_datetime(sales_df['timestamp'])
        sales_df['profit'] = sales_df['revenue'] - sales_df['cost']
        
        # --- SEZIONE METRICHE CHIAVE ---
        tot_ricavo = sales_df["revenue"].sum()
        tot_costo = sales_df["cost"].sum()
        tot_profitto = tot_ricavo - tot_costo
        tot_unita = sales_df["quantity"].sum()
        
        col_met1, col_met2, col_met3, col_met4 = st.columns(4)
        with col_met1: st.metric("Ricavo Totale", f"{VALUTA_SIMBOLO} {tot_ricavo:.2f}")
        with col_met2: st.metric("Costo Totale Merce", f"{VALUTA_SIMBOLO} {tot_costo:.2f}", help="Costo di acquisto della merce venduta")
        with col_met3: st.metric("Profitto Netto Attuale", f"{VALUTA_SIMBOLO} {tot_profitto:.2f}", delta=f"{VALUTA_SIMBOLO} {tot_ricavo:.2f} (Lordo)", help="Totale Ricavo - Totale Costo")
        with col_met4: st.metric("Unità Totali Vendute", f"{tot_unita} pz", help=f"Basato su {len(sales_df)} transazioni")
        
        st.divider()
        
        # --- SEZIONE GRAFICI ---
        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            # Grafico dell'andamento dei profitti nel tempo (cumulativo)
            sales_df_sorted = sales_df.sort_values('timestamp')
            sales_df_sorted['cumulative_profit'] = sales_df_sorted['profit'].cumsum()
            
            st.subheader("Andamento Profitto Netto (Cumulativo)")
            time_chart = alt.Chart(sales_df_sorted).mark_line(point=True).encode(
                x=alt.X('timestamp', title="Orario di Vendita"),
                y=alt.Y('cumulative_profit', title=f"Profitto Netto Totale ({VALUTA_SIMBOLO})"),
                tooltip=['timestamp', alt.Tooltip('cumulative_profit', format=f"{VALUTA_SIMBOLO} .2f")]
            ).interactive()
            st.altair_chart(time_chart, use_container_width=True)
            
        with col_chart2:
            # Grafico a ciambella dei ricavi per prodotto
            st.subheader("Ripartizione Ricavi per Prodotto")
            revenue_by_prod = sales_df.groupby('product_name')['revenue'].sum().reset_index()
            donut_chart = alt.Chart(revenue_by_prod).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("revenue", stack=True),
                color=alt.Color("product_name", legend=alt.Legend(title="Prodotto"), scale=alt.Scale(range=['#ff4b4b', '#4b86ff', '#ffb84b', '#4bff4b', '#d3d3d3'])), # Colori abbinati
                order=alt.Order("revenue", sort="descending"),
                tooltip=['product_name', alt.Tooltip('revenue', format=f"{VALUTA_SIMBOLO} .2f")]
            )
            st.altair_chart(donut_chart, use_container_width=True)
            
        st.divider()
        
        # --- SEZIONE REGISTRO VENDITE ---
        st.subheader("🧾 Registro Ultime Vendite")
        # Visualizza le ultime 10 vendite con formattazione carina
        recent_sales_df = sales_df.tail(10).sort_index(ascending=False)
        
        # Configurazione colonne tabella registro
        config_registro = {
            "timestamp": st.column_config.DatetimeColumn("Orario", format="HH:mm:ss", help="Ora esatta della transazione"),
            "product_name": st.column_config.TextColumn("Nome Prodotto"),
            "quantity": st.column_config.NumberColumn("Qta"),
            "revenue": st.column_config.NumberColumn(f"Ricavo ({VALUTA_SIMBOLO})", format=f"{VALUTA_SIMBOLO} %.2f"),
            "cost": st.column_config.NumberColumn(f"Costo ({VALUTA_SIMBOLO})", format=f"{VALUTA_SIMBOLO} %.2f"),
            "profit": st.column_config.NumberColumn(f"Profitto ({VALUTA_SIMBOLO})", format=f"{VALUTA_SIMBOLO} %.2f")
        }
        st.dataframe(recent_sales_df.drop(columns=['item_id']), column_config=config_registro, use_container_width=True, hide_index=True)
        
    else:
        st.info("Nessuna vendita registrata ancora. Vai alla scheda 'Cassa Veloce' per iniziare!")
