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

# Funzioni di caricamento
def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file)
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
            # Categorie aggiornate come richiesto
            cat = st.selectbox("Categoria", ["Luce", "Gas", "Acqua", "TARI", "Internet/Telefono", "Alimentari", "Manutenzione", "Altro"])
            importo = st.number_input("Importo (€)", min_value=0.0, step=0.01)
        
        with col_b:
            desc = st.text_input("Descrizione (es. Bolletta Enel)", placeholder="Ditta fornitrice...")
            periodo = st.text_input("Periodo di riferimento", placeholder="es. Gen-Feb 2024")
            
        submit = st.form_submit_button("Salva Spesa")

    if submit:
        nuova_riga = pd.DataFrame([[data_s, cat, desc, importo, periodo]], columns=df.columns)
        df = pd.concat([df, nuova_riga], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Spesa registrata!")
        st.rerun()

with tab2:
    st.subheader("Analisi dei costi")
    if not df.empty:
        # Metriche principali
        tot = df["Importo"].sum()
        st.metric("Totale Spese Registrate", f"€ {tot:,.2f}")
        
        c1, c2 = st.columns(2)
        with c1:
            # Grafico a torta per categorie
            fig_pie = px.pie(df, values='Importo', names='Categoria', title="Suddivisione per Categoria", hole=0.3)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with c2:
            # Grafico a barre per periodo
            df['Data'] = pd.to_datetime(df['Data'])
            df_m = df.resample('M', on='Data')['Importo'].sum().reset_index()
            fig_bar = px.bar(df_m, x='Data', y='Importo', title="Spesa Totale per Mese")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        st.subheader("Dettaglio Storico")
        st.dataframe(df.sort_values(by="Data", ascending=False), use_container_width=True)
    else:
        st.info("Nessun dato disponibile. Inserisci la prima spesa!")

with tab3:
    st.subheader("Gestione Modelli Ricorrenti")
    st.write("Configura qui le spese che si ripetono (es. Internet, Abbonamenti) per aggiungerle velocemente.")
    
    with st.expander("➕ Aggiungi un nuovo modello ricorrente"):
        with st.form("nuovo_modello"):
            r_cat = st.selectbox("Categoria", ["Luce", "Gas", "Acqua", "TARI", "Internet/Telefono", "Altro"])
            r_desc = st.text_input("Descrizione (es. Canone Fibra)")
            r_imp = st.number_input("Importo Standard (€)", min_value=0.0, step=0.01)
            r_submit = st.form_submit_button("Salva Modello")
            
            if r_submit:
                nuovo_m = pd.DataFrame([[date.today(), r_cat, r_desc, r_imp, "Ricorrente"]], columns=df_rec.columns)
                df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
                df_rec.to_csv(RECURRING_FILE, index=False)
                st.success("Modello salvato!")
                st.rerun()

    if not df_rec.empty:
        st.write("### I tuoi modelli")
        for i, row in df_rec.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.write(f"**{row['Descrizione']}** ({row['Categoria']})")
            col2.write(f"€ {row['Importo']}")
            if col3.button(f"Aggiungi ora", key=f"btn_{i}"):
                # Aggiunge la spesa al database principale con la data di oggi
                nuova_spesa = pd.DataFrame([[date.today(), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                df = pd.concat([df, nuova_spesa], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.toast(f"Aggiunta spesa: {row['Descrizione']}!")
    else:
        st.info("Non hai ancora creato modelli ricorrenti.")
