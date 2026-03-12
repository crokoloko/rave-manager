import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- CONFIGURAZIONE FILE ---
DB_FILE = "rave_data.json"

# --- FUNZIONI DI PERSISTENZA ---
def carica_dati():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {
        "inventory": {
            "Kit Leash+Acc": {"qta": 400, "costo": 0.80, "prezzo": 5.0},
            "Ventaglio": {"qta": 150, "costo": 0.80, "prezzo": 5.0},
            "Tappi Orecchie": {"qta": 1000, "costo": 0.05, "prezzo": 1.0}
        },
        "sales_history": []
    }

def salva_dati():
    dati = {
        "inventory": st.session_state.inventory,
        "sales_history": st.session_state.sales_history
    }
    with open(DB_FILE, "w") as f:
        json.dump(dati, f)

# --- INIZIALIZZAZIONE ---
if 'data_loaded' not in st.session_state:
    dati = carica_dati()
    st.session_state.inventory = dati["inventory"]
    st.session_state.sales_history = dati["sales_history"]
    st.session_state.data_loaded = True

st.set_page_config(page_title="Rave Manager", layout="centered")

# --- CSS PER MOBILE (Pulsanti enormi per dita veloci) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 100px;
        font-size: 24px !important;
        border-radius: 15px;
        margin-bottom: 15px;
        background-color: #2e2e2e;
        color: white;
        border: 2px solid #00ff00;
    }
    </style>
    """, unsafe_allow_html=True)

# --- LOGICA VENDITA ---
def registra_vendita(item_name, is_bundle=False):
    if is_bundle:
        # Logica Bundle: 1 Kit + 1 Ventaglio a 10€
        if st.session_state.inventory["Kit Leash+Acc"]["qta"] > 0 and st.session_state.inventory["Ventaglio"]["qta"] > 0:
            st.session_state.inventory["Kit Leash+Acc"]["qta"] -= 1
            st.session_state.inventory["Ventaglio"]["qta"] -= 1
            vendita = {
                "Orario": datetime.now().strftime("%H:%M:%S"),
                "Prodotto": "BUNDLE FULL",
                "Ricavo": 10.0,
                "Costo": st.session_state.inventory["Kit Leash+Acc"]["costo"] + st.session_state.inventory["Ventaglio"]["costo"]
            }
            st.session_state.sales_history.append(vendita)
            salva_dati()
            st.toast("💰 BUNDLE VENDUTO!")
        else:
            st.error("Scorte insufficienti per il Bundle!")
    else:
        if st.session_state.inventory[item_name]["qta"] > 0:
            st.session_state.inventory[item_name]["qta"] -= 1
            vendita = {
                "Orario": datetime.now().strftime("%H:%M:%S"),
                "Prodotto": item_name,
                "Ricavo": st.session_state.inventory[item_name]["prezzo"],
                "Costo": st.session_state.inventory[item_name]["costo"]
            }
            st.session_state.sales_history.append(vendita)
            salva_dati()
            st.toast(f"Venduto: {item_name} ✅")
        else:
            st.error(f"{item_name} ESAURITO!")

# --- UI ---
st.title("🕶️ RaveBusiness Mobile")

tab1, tab2, tab3 = st.tabs(["💸 CASSA", "📦 STOCK", "📈 REPORT"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔥 KIT\n5€"): registra_vendita("Kit Leash+Acc")
        if st.button("👂 TAPPI\n1€"): registra_vendita("Tappi Orecchie")
    with col2:
        if st.button("🌬️ VENT.\n5€"): registra_vendita("Ventaglio")
        if st.button("✨ BUNDLE\n10€"): registra_vendita(None, is_bundle=True)

with tab2:
    st.write("### Giacenze attuali")
    for item, info in st.session_state.inventory.items():
        st.write(f"**{item}**: {info['qta']} pz")
    
    if st.button("Ricarica Magazzino (Reset)"):
        if st.checkbox("Confermi reset totale?"):
            st.session_state.inventory = carica_dati()["inventory"]
            st.session_state.sales_history = []
            salva_dati()
            st.rerun()

with tab3:
    if st.session_state.sales_history:
        df = pd.DataFrame(st.session_state.sales_history)
        profitto = df["Ricavo"].sum() - df["Costo"].sum()
        st.metric("Profitto Netto", f"€ {profitto:.2f}", f"Incasso: {df['Ricavo'].sum()}€")
        st.dataframe(df.tail(10), use_container_width=True)
    else:
        st.info("Ancora nessuna vendita.")