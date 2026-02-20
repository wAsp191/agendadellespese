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

df = load_data(DATA_FILE)
df_rec = load_data(RECURRING_FILE)

st.title("🏠 Dashboard Spese Casa")

# --- SIDEBAR: FILTRI ANNO E CATEGORIA ---
st.sidebar.header("🔍 Filtri")

# Filtro Anno (fondamentale per ricominciare da capo ogni anno)
if not df.empty:
    anni_disponibili = sorted(df['Data'].dt.year.unique(), reverse=True)
else:
    anni_disponibili = [date.today().year]

anno_selezionato = st.sidebar.selectbox("Seleziona Anno", anni_disponibili)

# Filtro Categoria
categorie_disponibili = ["Tutte", "Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"]
filtro_cat = st.sidebar.selectbox("Filtra per Categoria", categorie_disponibili)

# --- LOGICA FILTRO ---
df_filtrato = df.copy()
# 1. Filtra per anno
df_filtrato = df_filtrato[df_filtrato['Data'].dt.year == anno_selezionato]
# 2. Filtra per categoria
if filtro_cat != "Tutte":
    df_filtrato = df_filtrato[df_filtrato["Categoria"] == filtro_cat]

# --- AGGIUNGI SPESA (+) ---
with st.expander("➕ **Aggiungi Nuova Spesa o Modello**", expanded=False):
    tab_nuova, tab_modello = st.tabs(["Singola Spesa", "Usa Ricorrente"])
    with tab_nuova:
        with st.form("form_veloce", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            d = c1.date_input("Data", date.today())
            cat = c1.selectbox("Categoria", ["Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"])
            imp = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
            per = c2.text_input("Periodo", placeholder="es. Gen-Feb")
            des = c3.text_input("Descrizione", placeholder="es. Bolletta Enel")
            if st.form_submit_button("Salva Spesa"):
                nuova_riga = pd.DataFrame([[pd.to_datetime(d), cat, des, imp, per]], columns=df.columns)
                df = pd.concat([df, nuova_riga], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()
    # (Tab Modelli invariato...)

# --- DASHBOARD ---
if not df_filtrato.empty:
    st.subheader(f"Statistiche anno {anno_selezionato}")
    totale_anno = df_filtrato["Importo"].sum()
    st.metric(f"Totale {filtro_cat} ({anno_selezionato})", f"€ {totale_anno:,.2f}")

    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = px.pie(df_filtrato, values='Importo', names='Categoria', title="Distribuzione Annuale", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Preparazione dati per grafico mensile (Gen-Dic)
        mesi_nomi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        df_m = df_filtrato.copy()
        df_m['Mese_Num'] = df_m['Data'].dt.month
        resoconto_mesi = df_m.groupby('Mese_Num')['Importo'].sum().reindex(range(1, 13), fill_value=0).reset_index()
        resoconto_mesi['Mese'] = mesi_nomi
        
        fig_area = px.area(resoconto_mesi, x='Mese', y='Importo', 
                          title=f"Andamento Mensile {anno_selezionato}",
                          markers=True, line_shape="spline")
        
        # Imposta l'asse Y per essere leggibile e l'asse X fisso sui 12 mesi
        fig_area.update_layout(xaxis_title="Mese", yaxis_title="Spesa (€)", yaxis_range=[0, max(resoconto_mesi['Importo'].max() + 50, 800)])
        st.plotly_chart(fig_area, use_container_width=True)

    st.divider()
    st.subheader("📜 Storico Selezionato")
    df_display = df_filtrato.copy().sort_values(by="Data", ascending=False)
    df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_display, use_container_width=True)

    with st.expander("🗑️ Elimina una spesa"):
        opzioni = [f"{i}: {r['Data'].strftime('%d/%m/%Y')} - {r['Descrizione']} ({r['Importo']}€)" for i, r in df_filtrato.iterrows()]
        scelta = st.selectbox("Seleziona riga", opzioni)
        if st.button("Elimina Definitivamente"):
            idx = int(scelta.split(":")[0])
            df = df.drop(idx)
            df.to_csv(DATA_FILE, index=False)
            st.rerun()
else:
    st.info(f"Nessun dato per l'anno {anno_selezionato}. Inizia ad aggiungere spese!")
