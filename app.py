import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Tracker", layout="wide")

# File dove verranno salvati i dati
DATA_FILE = "spese_casa.csv"

# Funzione per caricare i dati
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Data", "Categoria", "Descrizione", "Importo"])

# Inizializzazione dati
df = load_data()

st.title("🏠 Gestione Spese e Bollette")

# --- SIDEBAR PER INSERIMENTO ---
st.sidebar.header("Aggiungi Nuova Spesa")
with st.sidebar.form("form_spesa"):
    data_spesa = st.date_input("Data", date.today())
    categoria = st.selectbox("Categoria", ["Bollette (Luce/Gas)", "Affitto/Mutuo", "Spesa Alimentare", "Internet/Telefono", "Manutenzione", "Altro"])
    descrizione = st.text_input("Descrizione (es. Bolletta Enel)")
    importo = st.number_input("Importo (€)", min_value=0.0, step=0.01, format="%.2f")
    
    submit = st.form_submit_button("Salva Spesa")

if submit:
    nuova_riga = pd.DataFrame([[data_spesa, categoria, descrizione, importo]], columns=df.columns)
    df = pd.concat([df, nuova_riga], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.sidebar.success("Spesa salvata con successo!")
    st.rerun()

# --- DASHBOARD PRINCIPALE ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Storico Spese")
    if not df.empty:
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.info("Nessuna spesa registrata al momento.")

with col2:
    st.subheader("Riepilogo Totale")
    totale = df["Importo"].sum()
    st.metric("Totale Speso", f"€ {totale:,.2f}")
    
    if not df.empty:
        # Calcolo per categoria
        spese_per_cat = df.groupby("Categoria")["Importo"].sum().reset_index()
        fig_pie = px.pie(spese_per_cat, values='Importo', names='Categoria', hole=0.4, title="Distribuzione Spese")
        st.plotly_chart(fig_pie, use_container_width=True)

# --- GRAFICO TEMPORALE ---
if not df.empty:
    st.divider()
    st.subheader("Andamento Mensile")
    df['Data'] = pd.to_datetime(df['Data'])
    df_mensile = df.resample('M', on='Data')['Importo'].sum().reset_index()
    fig_line = px.line(df_mensile, x='Data', y='Importo', markers=True, title="Spese nel Tempo")
    st.plotly_chart(fig_line, use_container_width=True)
