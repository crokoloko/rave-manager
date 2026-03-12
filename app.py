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

