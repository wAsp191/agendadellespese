import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Pro", layout="wide", page_icon="📊")

# File Database
DATA_FILE = "spese_casa_v2.csv"
RECURRING_FILE = "modelli_ricorrenti.csv"

# Funzioni di caricamento con correzione automatica del formato data
def load_data(file):
    if os.path.exists(file):
        df_loaded = pd.read_csv(file)
        # Forza la conversione in data e gestisce eventuali errori
        if not df_loaded.empty and "Data" in df_loaded.columns:
            df_loaded['Data'] = pd.to_datetime(df_loaded['Data'], errors='coerce')
            # Rimuove eventuali righe dove la data è diventata NaT (corrotta)
            df_loaded = df_loaded.dropna(subset=['Data'])
        return df_loaded
    return pd.DataFrame(columns=["Data", "Categoria", "Descrizione", "Importo", "Periodo"])

# Inizializzazione dati
df = load_data(DATA_FILE)
df_rec = load_data(RECURRING_FILE)

st.title("📊 Gestione Spese e Bollette Avanzata")

# --- TABS PER ORGANIZZAZIONE ---
tab1, tab2, tab3 = st.tabs(["➕ Inserimento", "📈 Statistiche", "🔁 Spese Ricorrenti"])

with tab1:
    st.subheader("Registra una nuova spesa")
    with st.form("nuova_spesa_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        with col_a:
            data_s = st.date_input("Data Pagamento", date.today())
            cat = st.selectbox("Categoria", ["Luce", "Gas", "Acqua", "TARI", "Internet/Telefono", "Alimentari", "Manutenzione", "Altro"])
            importo = st.number_input("Importo (€)", min_value=0.0, step=0.01)
        
        with col_b:
            desc = st.text_input("Descrizione (es. Bolletta Enel)", placeholder="Ditta fornitrice...")
            periodo = st.text_input("Periodo di riferimento", placeholder="es. Gen-Feb 2024")
            
        submit = st.form_submit_button("Salva Spesa")

    if submit:
        # Salviamo la data come stringa ISO per massima compatibilità
        nuova_riga = pd.DataFrame([[pd.to_datetime(data_s), cat, desc, importo, periodo]], columns=["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
        df = pd.concat([df, nuova_riga], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Spesa registrata!")
        st.rerun()

with tab2:
    st.subheader("Analisi dei costi")
    if not df.empty:
        tot = df["Importo"].sum()
        st.metric("Totale Spese Registrate", f"€ {tot:,.2f}")
        
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(df, values='Importo', names='Categoria', title="Suddivisione per Categoria", hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            # Raggruppamento mensile sicuro
            df_temp = df.copy()
            df_temp['Mese'] = df_temp['Data'].dt.to_period('M').astype(str)
            df_m = df_temp.groupby('Mese')['Importo'].sum().reset_index()
            fig_bar = px.bar(df_m, x='Mese', y='Importo', title="Spesa Totale per Mese")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.subheader("Dettaglio Storico")
        # Visualizzazione formattata per l'utente
        df_display = df.copy()
        df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_display.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.info("Nessun dato disponibile.")

with tab3:
    st.subheader("Gestione Modelli Ricorrenti")
    with st.expander("➕ Aggiungi un nuovo modello"):
        with st.form("nuovo_modello"):
            r_cat = st.selectbox("Categoria", ["Luce", "Gas", "Acqua", "TARI", "Internet/Telefono", "Altro"])
            r_desc = st.text_input("Descrizione")
            r_imp = st.number_input("Importo Standard (€)", min_value=0.0, step=0.01)
            r_submit = st.form_submit_button("Salva Modello")
            
            if r_submit:
                nuovo_m = pd.DataFrame([[pd.to_datetime(date.today()), r_cat, r_desc, r_imp, "Ricorrente"]], columns=["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
                df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
                df_rec.to_csv(RECURRING_FILE, index=False)
                st.success("Modello salvato!")
                st.rerun()

    if not df_rec.empty:
        for i, row in df_rec.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{row['Descrizione']}**")
            col2.write(f"€ {row['Importo']}")
            if col3.button(f"Aggiungi", key=f"btn_{i}"):
                nuova_spesa = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                df = pd.concat([df, nuova_spesa], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.toast("Aggiunta!")
                st.rerun()
