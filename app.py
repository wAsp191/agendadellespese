import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io
from openpyxl.styles import Font, Alignment

# --- 1. SICUREZZA ---
PASSWORD_ACCESSO = "poggio2026" 

# Configurazione Pagina (Mobile First) - Ripristinata icona Sacco di Soldi
st.set_page_config(page_title="Bilancio Casa", layout="centered", page_icon="💰")

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
    st.stop()

# --- 2. LOGICA DATI E CATEGORIE ---
DATA_FILE = "spese_casa_v4.csv"
RECURRING_FILE = "modelli_ricorrenti_v4.csv"

# Definizione rigorosa categorie e colori
color_map = {
    "Acqua": "#0000FF",         # Blu
    "Luce": "#FFFF00",          # Giallo
    "Gas": "#008000",           # Verde
    "Tari": "#000000",          # Nero
    "Tel/Internet": "#FFA500",  # Arancione
    "Alimentari": "#800080",      # Viola
    "Abbonamenti": "#808080",   # Grigio
    "Altro": "#A9A9A9"          # Grigio scuro
}
cat_lista_clean = list(color_map.keys())
cat_lista_filtro = ["Tutte"] + cat_lista_clean

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

# --- FUNZIONE EXCEL POTENZIATA ---
def to_excel_pro(df_to_download):
    output = io.BytesIO()
    df_excel = df_to_download.copy()
    df_excel['Data'] = df_excel['Data'].dt.strftime('%d/%m/%Y')
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Report Spese')
        workbook = writer.book
        worksheet = writer.sheets['Report Spese']
        
        bold_font = Font(bold=True, size=12)
        center_alig = Alignment(horizontal='center')

        # Formattazione intestazioni e celle
        for row in worksheet.iter_rows(min_row=1, max_row=len(df_excel)+1):
            for cell in row:
                cell.alignment = Alignment(vertical='center', horizontal='left')
                if cell.row == 1:
                    cell.font = bold_font
            # Aumenta altezza riga per leggibilità
            worksheet.row_dimensions[row[0].row].height = 25

        # Larghezza colonne maggiorata
        for col in worksheet.columns:
            worksheet.column_dimensions[col[0].column_letter].width = 25
            
        # Riga Totale
        last_row = len(df_excel) + 2
        worksheet.cell(row=last_row, column=3, value="TOTALE GENERALE:").font = bold_font
        worksheet.cell(row=last_row, column=4, value=df_to_download['Importo'].sum()).font = bold_font
        worksheet.row_dimensions[last_row].height = 30

    return output.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.header("💰 Gestione")
    anni = sorted(df['Data'].dt.year.unique(), reverse=True) if not df.empty else [date.today().year]
    anno_sel = st.selectbox("Seleziona Anno", anni)
    cat_sel = st.selectbox("Filtra Categoria", cat_lista_filtro)
    
    st.divider()
    # Pulsante Excel ripristinato e visibile
    if not df.empty:
        df_f_excel = df[df['Data'].dt.year == anno_sel].copy()
        if cat_sel != "Tutte":
            df_f_excel = df_f_excel[df_f_excel["Categoria"] == cat_sel]
        
        if not df_f_excel.empty:
            st.download_button(
                label="📥 Scarica Report Excel",
                data=to_excel_pro(df_f_excel),
                file_name=f"Spese_{anno_sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    if st.button("Esci (Logout)", use_container_width=True):
        st.session_state["autenticato"] = False
        st.rerun()

# Filtraggio dati per la dashboard
df_f = df[df['Data'].dt.year == anno_sel].copy() if not df.empty else pd.DataFrame()
if cat_sel != "Tutte" and not df_f.empty:
    df_f = df_f[df_f["Categoria"] == cat_sel]

# --- INTERFACCIA ---
st.title("💰 Spese di Casa")

with st.expander("➕ **AGGIUNGI NUOVA VOCE**", expanded=False):
    t1, t2 = st.tabs(["✍️ Manuale", "🔁 Modelli"])
    with t1:
        with st.form("fm", clear_on_submit=True):
            d = st.date_input("Data", date.today())
            c = st.selectbox("Categoria", cat_lista_clean)
            i = st.number_input("Importo (€)", min_value=0.0, step=0.01)
            p = st.text_input("Periodo (es. Gen-Feb)")
            ds = st.text_input("Nota/Descrizione")
            if st.form_submit_button("SALVA SPESA", use_container_width=True):
                nuova = pd.DataFrame([[pd.to_datetime(d), c, ds, i, p]], columns=df.columns)
                df = pd.concat([df, nuova], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()
    with t2:
        if df_rec.empty: st.info("Crea un modello in fondo alla pagina.")
        for idx, row in df_rec.iterrows():
            if st.button(f"📌 {row['Descrizione']} (€{row['Importo']})", key=f"r_{idx}", use_container_width=True):
                nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                df = pd.concat([df, nuova_s], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.rerun()

if not df_f.empty:
    st.metric(f"Totale {cat_sel}", f"€ {df_f['Importo'].sum():,.2f}")
    
    # 1. Grafico a Torta con colori fissi
    df_pie = df_f.groupby('Categoria')['Importo'].sum().reset_index()
    fig_pie = px.pie(df_pie, values='Importo', names='Categoria', 
                     hole=0.5, title="Suddivisione Spese",
                     color='Categoria', color_discrete_map=color_map)
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # 2. Grafico Andamento Mensile Migliorato (Istogramma a barre)
    mesi_ita = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    df_m = df_f.copy()
    df_m['M_Num'] = df_m['Data'].dt.month
    res = df_m.groupby(['M_Num', 'Categoria'])['Importo'].sum().reset_index()
    
    # Creazione grafico a barre raggruppate per una chiarezza massima
    fig_bar = px.bar(res, x='M_Num', y='Importo', color='Categoria',
                     title=f"Andamento Mensile {anno_sel}",
                     labels={'M_Num': 'Mese', 'Importo': 'Spesa (€)'},
                     color_discrete_map=color_map,
                     barmode='group')
    
    fig_bar.update_layout(xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), ticktext=mesi_ita))
    st.plotly_chart(fig_bar, use_container_width=True)

    # Storico
    st.subheader("📜 Ultime voci inserite")
    df_mini = df_f[['Data', 'Categoria', 'Descrizione', 'Importo']].copy().sort_values("Data", ascending=False)
    df_mini['Data'] = df_mini['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_mini, use_container_width=True, hide_index=True)
    
    with st.expander("🗑️ Elimina errore"):
        idx_del = st.selectbox("Seleziona spesa", df_f.index, 
                               format_func=lambda x: f"{df.loc[x,'Data'].strftime('%d/%m')} - {df.loc[x,'Descrizione']} (€{df.loc[x,'Importo']})")
        if st.button("ELIMINA DEFINITIVAMENTE", use_container_width=True):
            df = df.drop(idx_del)
            df.to_csv(DATA_FILE, index=False)
            st.rerun()
else:
    st.info("Nessuna spesa trovata per i filtri selezionati.")

# Configurazione Modelli
st.divider()
with st.expander("⚙️ CONFIGURA MODELLI RICORRENTI"):
    with st.form("f_mod"):
        c1 = st.selectbox("Categoria", cat_lista_clean)
        c2 = st.text_input("Nome Modello (es. Bolletta Luce)")
        c3 = st.number_input("Importo Standard", min_value=0.0)
        if st.form_submit_button("CREA MODELLO", use_container_width=True):
            nuovo_m = pd.DataFrame([[c1, c2, c3, "Mensile", date.today()]], columns=["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
            df_rec.to_csv(RECURRING_FILE, index=False)
            st.rerun()
