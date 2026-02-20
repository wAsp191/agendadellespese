import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io
from openpyxl.styles import Font

# --- 1. SICUREZZA ---
PASSWORD_ACCESSO = "poggio2026" # <--- CAMBIA QUESTA PASSWORD!

# Configurazione Pagina (Mobile First)
st.set_page_config(page_title="Bilancio Casa", layout="centered", page_icon="🏦")

# Inizializzazione sessione per login
if "autenticato" not in st.session_state:
    st.session_state["autenticato"] = False

if not st.session_state["autenticato"]:
    st.title("🔐 Accesso Riservato")
    pwd = st.text_input("Inserisci la password di famiglia:", type="password")
    if st.button("Entra"):
        if pwd == PASSWORD_ACCESSO:
            st.session_state["autenticato"] = True
            st.rerun()
        else:
            st.error("Password errata!")
    st.stop() # Blocca l'esecuzione qui se non autenticato

# --- 2. LOGICA APP (Dopo Login) ---
DATA_FILE = "spese_casa_v4.csv"
RECURRING_FILE = "modelli_ricorrenti_v4.csv"

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df_loaded = pd.read_csv(file)
            if not df_loaded.empty:
                df_loaded['Data'] = pd.to_datetime(df_loaded['Data'], errors='coerce')
                df_loaded = df_loaded.dropna(subset=['Data'])
            return df_loaded
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

df = load_data(DATA_FILE, ["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
df_rec = load_data(RECURRING_FILE, ["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])

# --- SIDEBAR (Ottimizzata per Mobile) ---
with st.sidebar:
    st.header("⚙️ Opzioni")
    anni = sorted(df['Data'].dt.year.unique(), reverse=True) if not df.empty else [date.today().year]
    anno_sel = st.selectbox("Anno", anni)
    cat_lista = ["Tutte", "Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"]
    cat_sel = st.selectbox("Filtra Categoria", cat_lista)
    
    if st.button("Esci (Logout)"):
        st.session_state["autenticato"] = False
        st.rerun()

# Filtraggio
df_f = df[df['Data'].dt.year == anno_sel].copy() if not df.empty else pd.DataFrame()
if cat_sel != "Tutte" and not df_f.empty:
    df_f = df_f[df_f["Categoria"] == cat_sel]

# --- INTERFACCIA SMARTPHONE FRIENDLY ---
st.title("🏦 Spese di Casa")

# Tasto + (Molto grande per il pollice)
with st.expander("➕ **AGGIUNGI SPESA**", expanded=False):
    t1, t2 = st.tabs(["Nuova", "Modelli"])
    with t1:
        with st.form("fm", clear_on_submit=True):
            d = st.date_input("Data", date.today())
            c = st.selectbox("Cosa?", cat_lista[1:])
            i = st.number_input("Quanto (€)", min_value=0.0, step=0.01)
            p = st.text_input("Periodo (es. Gen-Feb)")
            ds = st.text_input("Nota (es. Enel)")
            if st.form_submit_button("SALVA ORA", use_container_width=True):
                nuova = pd.DataFrame([[pd.to_datetime(d), c, ds, i, p]], columns=df.columns)
                df = pd.concat([df, nuova], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()
    with t2:
        for idx, row in df_rec.iterrows():
            if st.button(f"📌 {row['Descrizione']} (€{row['Importo']})", key=f"r_{idx}", use_container_width=True):
                nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                df = pd.concat([df, nuova_s], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()

# Dashboard Mobile (Verticale)
if not df_f.empty:
    st.metric(f"Totale {cat_sel}", f"€ {df_f['Importo'].sum():,.2f}")
    
    # Grafico a torta (ridimensionato)
    df_pie = df_f.groupby('Categoria')['Importo'].sum().reset_index()
    st.plotly_chart(px.pie(df_pie, values='Importo', names='Categoria', hole=0.4, title="Suddivisione"), use_container_width=True)
    
    # Grafico area (ridimensionato)
    mesi = ["G", "F", "M", "A", "M", "G", "L", "A", "S", "O", "N", "D"]
    df_m = df_f.copy()
    df_m['M_Num'] = df_m['Data'].dt.month
    res = df_m.groupby('M_Num')['Importo'].sum().reindex(range(1, 13), fill_value=0).reset_index()
    res['Mese'] = mesi
    st.plotly_chart(px.area(res, x='Mese', y='Importo', title="Andamento"), use_container_width=True)

    # Storico Semplificato
    st.subheader("📜 Ultime voci")
    df_mini = df_f[['Data', 'Descrizione', 'Importo']].copy().sort_values("Data", ascending=False)
    df_mini['Data'] = df_mini['Data'].dt.strftime('%d/%m')
    st.dataframe(df_mini, use_container_width=True, hide_index=True)
else:
    st.info("Nessun dato. Usa il tasto + in alto!")

# Gestione Modelli
with st.expander("⚙️ Configura Modelli"):
    with st.form("f_mod"):
        c1 = st.selectbox("Categoria", cat_lista[1:])
        c2 = st.text_input("Nome Modello")
        c3 = st.number_input("Importo", min_value=0.0)
        if st.form_submit_button("Crea Modello", use_container_width=True):
            nuovo_m = pd.DataFrame([[c1, c2, c3, "Mensile", date.today()]], columns=["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
            df_rec.to_csv(RECURRING_FILE, index=False)
            st.rerun()
