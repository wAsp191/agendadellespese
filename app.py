import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Pro", layout="wide", page_icon="💰")

# Usiamo nomi file v4 per coerenza con l'ultimo salvataggio
DATA_FILE = "spese_casa_v4.csv"
RECURRING_FILE = "modelli_ricorrenti_v4.csv"

# --- FUNZIONE CARICAMENTO CON PULIZIA PROFONDA ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df_loaded = pd.read_csv(file)
            if not df_loaded.empty:
                # Forza la colonna Data a essere di tipo datetime
                df_loaded['Data'] = pd.to_datetime(df_loaded['Data'], errors='coerce')
                # Rimuove righe dove la data è fallita (NaT)
                df_loaded = df_loaded.dropna(subset=['Data'])
                # Assicura che le altre colonne esistano
                for col in columns:
                    if col not in df_loaded.columns:
                        df_loaded[col] = ""
            return df_loaded
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Inizializzazione
df = load_data(DATA_FILE, ["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
df_rec = load_data(RECURRING_FILE, ["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])

st.title("🏠 Dashboard Spese Casa")

# --- SIDEBAR E FILTRI ---
st.sidebar.header("🔍 Filtri e Strumenti")

# Calcolo anni sicuro
if not df.empty:
    anni_disponibili = sorted(df['Data'].dt.year.unique(), reverse=True)
else:
    anni_disponibili = [date.today().year]

anno_selezionato = st.sidebar.selectbox("Seleziona Anno", anni_disponibili)
categorie_lista = ["Tutte", "Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"]
filtro_cat = st.sidebar.selectbox("Filtra per Categoria", categorie_lista)

# Logica Filtro (Senza crash ora)
df_filtrato = df.copy()
if not df_filtrato.empty:
    df_filtrato = df_filtrato[df_filtrato['Data'].dt.year == anno_selezionato]
    if filtro_cat != "Tutte":
        df_filtrato = df_filtrato[df_filtrato["Categoria"] == filtro_cat]

# --- FUNZIONE EXPORT EXCEL ---
def to_excel(df_to_download):
    output = io.BytesIO()
    df_excel = df_to_download.copy()
    if not df_excel.empty:
        df_excel['Data'] = df_excel['Data'].dt.strftime('%d/%m/%Y')
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Spese')
    return output.getvalue()

if not df_filtrato.empty:
    excel_data = to_excel(df_filtrato)
    st.sidebar.download_button(
        label="📥 Esporta Filtro in Excel",
        data=excel_data,
        file_name=f"Report_Spese_{anno_selezionato}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- AGGIUNGI SPESA (+) ---
with st.expander("➕ **Aggiungi Nuova Spesa o Modello**", expanded=False):
    tab_nuova, tab_modello = st.tabs(["Nuova Spesa", "Spese Ricorrenti"])
    with tab_nuova:
        with st.form("form_veloce", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            d = c1.date_input("Data", date.today())
            cat = c1.selectbox("Categoria", categorie_lista[1:])
            imp = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
            per = c2.text_input("Periodo", placeholder="es. Gen-Feb")
            des = c3.text_input("Descrizione", placeholder="es. Bolletta Enel")
            if st.form_submit_button("Salva Spesa"):
                nuova_riga = pd.DataFrame([[pd.to_datetime(d), cat, des, imp, per]], columns=["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
                df = pd.concat([df, nuova_riga], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()
    with tab_modello:
        if not df_rec.empty:
            for i, row in df_rec.iterrows():
                col_a, col_b = st.columns([4, 1])
                col_a.write(f"**{row['Descrizione']}** - €{row['Importo']}")
                if col_b.button(f"Inserisci", key=f"rec_{i}"):
                    nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
                    df = pd.concat([df, nuova_s], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.rerun()

# --- DASHBOARD ---
if not df_filtrato.empty:
    st.divider()
    df_pie = df_filtrato.groupby('Categoria')['Importo'].sum().reset_index()
    df_pie['Etichetta'] = df_pie.apply(lambda r: f"{r['Categoria']}: €{r['Importo']:,.2f}", axis=1)

    col_left, col_right = st.columns(2)
    with col_left:
        fig_pie = px.pie(df_pie, values='Importo', names='Etichetta', title="Budget Annuale", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_right:
        mesi_nomi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        df_m = df_filtrato.copy()
        df_m['Mese_Num'] = df_m['Data'].dt.month
        resoconto_mesi = df_m.groupby('Mese_Num')['Importo'].sum().reindex(range(1, 13), fill_value=0).reset_index()
        resoconto_mesi['Mese'] = mesi_nomi
        fig_area = px.area(resoconto_mesi, x='Mese', y='Importo', title=f"Trend {anno_selezionato}")
        fig_area.update_layout(yaxis_range=[0, max(resoconto_mesi['Importo'].max() + 100, 800)])
        st.plotly_chart(fig_area, use_container_width=True)

    st.divider()
    st.subheader("📜 Storico")
    df_display = df_filtrato.copy().sort_values(by="Data", ascending=False)
    df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_display, use_container_width=True)
    
    with st.expander("🗑️ Elimina riga"):
        idx_to_del = st.selectbox("Seleziona spesa", df_filtrato.index, 
                                  format_func=lambda x: f"{df.loc[x, 'Data'].strftime('%d/%m/%Y')} - {df.loc[x, 'Descrizione']} (€{df.loc[x, 'Importo']})")
        if st.button("Conferma Eliminazione"):
            df = df.drop(idx_to_del)
            df.to_csv(DATA_FILE, index=False)
            st.rerun()
else:
    st.info("Nessun dato trovato per i filtri selezionati.")

# --- MODELLI (IN FONDO) ---
st.divider()
with st.expander("⚙️ Modelli Ricorrenti"):
    with st.form("nuovo_mod_form"):
        c1, c2, c3, c4 = st.columns(4)
        rcat = c1.selectbox("Categoria", categorie_lista[1:])
        rdes = c2.text_input("Nome")
        rimp = c3.number_input("Importo", min_value=0.0)
        rcad = c4.selectbox("Cadenza", ["Mensile", "Bimestrale", "Annuale"])
        if st.form_submit_button("Salva"):
            nuovo_m = pd.DataFrame([[rcat, rdes, rimp, rcad, date.today()]], columns=["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
            df_rec.to_csv(RECURRING_FILE, index=False)
            st.rerun()
