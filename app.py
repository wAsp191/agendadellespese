import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Pro", layout="wide", page_icon="💰")

DATA_FILE = "spese_casa_v3.csv"
RECURRING_FILE = "modelli_ricorrenti_v3.csv"

def load_data(file):
    if os.path.exists(file):
        df_loaded = pd.read_csv(file)
        if not df_loaded.empty and "Data" in df_loaded.columns:
            df_loaded['Data'] = pd.to_datetime(df_loaded['Data'], errors='coerce')
            df_loaded = df_loaded.dropna(subset=['Data'])
        return df_loaded
    return pd.DataFrame(columns=["Data", "Categoria", "Descrizione", "Importo", "Periodo"])

# Inizializzazione
df = load_data(DATA_FILE)
df_rec = load_data(RECURRING_FILE)

st.title("🏠 Dashboard Spese Casa")

# --- SEZIONE AGGIUNGI SPESA (+) ---
with st.expander("➕ **Aggiungi Nuova Spesa o Modello**", expanded=False):
    tab_nuova, tab_modello = st.tabs(["Singola Spesa", "Usa Ricorrente"])
    
    with tab_nuova:
        with st.form("form_veloce", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                d = st.date_input("Data", date.today())
                c = st.selectbox("Categoria", ["Luce", "Gas", "Acqua", "Tari", "Telefono/Internet", "Alimentari", "Manutenzione", "Abbonamenti", "Altro"])
            with col2:
                imp = st.number_input("Importo (€)", min_value=0.0, step=0.01)
                per = st.text_input("Periodo", placeholder="es. Gen-Feb")
            with col3:
                des = st.text_input("Descrizione", placeholder="es. Bolletta Enel")
                sub = st.form_submit_button("Salva Spesa")
            
            if sub:
                nuova_riga = pd.DataFrame([[pd.to_datetime(d), c, des, imp, per]], columns=df.columns)
                df = pd.concat([df, nuova_riga], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Registrata!")
                st.rerun()
    
    with tab_modello:
        if not df_rec.empty:
            for i, row in df_rec.iterrows():
                if st.button(f"Aggiungi {row['Descrizione']} (€{row['Importo']})", key=f"rec_{i}"):
                    nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                    df = pd.concat([df, nuova_s], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.rerun()
        else:
            st.info("Crea prima un modello nelle impostazioni in fondo alla pagina.")

# --- DASHBOARD GRAFICI (VISIBILE SUBITO) ---
if not df.empty:
    st.divider()
    totale_generale = df["Importo"].sum()
    st.metric("Totale Speso", f"€ {totale_generale:,.2f}")

    col_left, col_right = st.columns(2)
    
    with col_left:
        fig_pie = px.pie(df, values='Importo', names='Categoria', title="Distribuzione per Categoria", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_right:
        df_temp = df.copy()
        df_temp['Mese'] = df_temp['Data'].dt.to_period('M').astype(str)
        df_m = df_temp.groupby('Mese')['Importo'].sum().reset_index()
        fig_bar = px.bar(df_m, x='Mese', y='Importo', title="Andamento Mese per Mese", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- STORICO ED ELIMINAZIONE ---
    st.subheader("📜 Storico e Modifiche")
    df_display = df.copy().sort_values(by="Data", ascending=False)
    df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(df_display, use_container_width=True)
    
    with st.expander("🗑️ Elimina una spesa errata"):
        opzioni_elimina = [f"{i}: {r['Data'].strftime('%d/%m/%Y')} - {r['Descrizione']} ({r['Importo']}€)" for i, r in df.iterrows()]
        scelta = st.selectbox("Seleziona la riga da rimuovere", options=opzioni_elimina)
        if st.button("Elimina Definitivamente", type="primary"):
            index_da_eliminare = int(scelta.split(":")[0])
            df = df.drop(index_da_eliminare)
            df.to_csv(DATA_FILE, index=False)
            st.warning("Voce eliminata.")
            st.rerun()

else:
    st.info("Benvenuto! Clicca sul tasto '+' in alto per inserire la tua prima spesa.")

# --- SEZIONE MODELLI (IN FONDO) ---
st.divider()
with st.expander("⚙️ Configura Modelli Ricorrenti"):
    with st.form("nuovo_mod_form"):
        c1, c2, c3 = st.columns(3)
        rc = c1.selectbox("Categoria", ["Luce", "Gas", "Acqua", "TARI", "Internet", "Altro"])
        rd = c2.text_input("Descrizione Modello")
        ri = c3.number_input("Importo Standard", min_value=0.0)
        if st.form_submit_button("Salva Modello"):
            nuovo_m = pd.DataFrame([[pd.to_datetime(date.today()), rc, rd, ri, "Modello"]], columns=df.columns)
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
            df_rec.to_csv(RECURRING_FILE, index=False)
            st.rerun()
