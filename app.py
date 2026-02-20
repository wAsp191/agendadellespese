import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io
from openpyxl.styles import Font, Alignment

# --- 1. SICUREZZA ---
PASSWORD_ACCESSO = "poggio2026" 

# Configurazione Pagina (Mobile First)
st.set_page_config(page_title="Bilancio Casa", layout="centered", page_icon="💰")

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

# Mappa Colori Rigorosa
color_map = {
    "Acqua": "#0000FF",         # Blu
    "Luce": "#FFFF00",          # Giallo
    "Gas": "#008000",           # Verde
    "Tari": "#000000",          # Nero
    "Tel/Internet": "#FFA500",  # Arancione
    "Alimenti": "#800080",      # Viola
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

# --- FUNZIONE EXCEL PRO ---
def to_excel_pro(df_to_download):
    output = io.BytesIO()
    df_excel = df_to_download.copy()
    df_excel['Data'] = df_excel['Data'].dt.strftime('%d/%m/%Y')
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Report Spese')
        workbook = writer.book
        worksheet = writer.sheets['Report Spese']
        bold_font = Font(bold=True, size=12)
        
        for row in worksheet.iter_rows(min_row=1, max_row=len(df_excel)+1):
            for cell in row:
                cell.alignment = Alignment(vertical='center', horizontal='left')
                if cell.row == 1: cell.font = bold_font
            worksheet.row_dimensions[row[0].row].height = 25

        for col in worksheet.columns:
            worksheet.column_dimensions[col[0].column_letter].width = 25
            
        last_row = len(df_excel) + 2
        worksheet.cell(row=last_row, column=3, value="TOTALE GENERALE:").font = bold_font
        worksheet.cell(row=last_row, column=4, value=df_to_download['Importo'].sum()).font = bold_font
        worksheet.row_dimensions[last_row].height = 30
    return output.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.header("💰 Opzioni")
    anni = sorted(df['Data'].dt.year.unique(), reverse=True) if not df.empty else [date.today().year]
    anno_sel = st.sidebar.selectbox("Anno", anni)
    cat_sel = st.sidebar.selectbox("Filtra Categoria", cat_lista_filtro)
    
    if not df.empty:
        df_f_excel = df[df['Data'].dt.year == anno_sel].copy()
        if cat_sel != "Tutte": df_f_excel = df_f_excel[df_f_excel["Categoria"] == cat_sel]
        if not df_f_excel.empty:
            st.download_button("📥 Scarica Report Excel", data=to_excel_pro(df_f_excel), 
                             file_name=f"Spese_{anno_sel}.xlsx", use_container_width=True)
    
    if st.button("Esci (Logout)", use_container_width=True):
        st.session_state["autenticato"] = False
        st.rerun()

# Filtraggio
df_f = df[df['Data'].dt.year == anno_sel].copy() if not df.empty else pd.DataFrame()
if cat_sel != "Tutte" and not df_f.empty:
    df_f = df_f[df_f["Categoria"] == cat_sel]

# --- UI PRINCIPALE ---
st.title("💰 Spese di Casa")

with st.expander("➕ **AGGIUNGI SPESA**", expanded=False):
    t1, t2 = st.tabs(["✍️ Manuale", "🔁 Modelli"])
    with t1:
        with st.form("fm", clear_on_submit=True):
            d = st.date_input("Data", date.today())
            c = st.selectbox("Categoria", cat_lista_clean)
            i = st.number_input("Importo (€)", min_value=0.0, step=0.01)
            p = st.text_input("Periodo (es. Gen-Feb)")
            ds = st.text_input("Nota")
            if st.form_submit_button("SALVA", use_container_width=True):
                nuova = pd.DataFrame([[pd.to_datetime(d), c, ds, i, p]], columns=df.columns)
                df = pd.concat([df, nuova], ignore_index=True); df.to_csv(DATA_FILE, index=False)
                st.rerun()
    with t2:
        for idx, row in df_rec.iterrows():
            if st.button(f"📌 {row['Descrizione']} (€{row['Importo']})", key=f"r_{idx}", use_container_width=True):
                nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                df = pd.concat([df, nuova_s], ignore_index=True); df.to_csv(DATA_FILE, index=False)
                st.rerun()

if not df_f.empty:
    st.metric(f"Totale {cat_sel}", f"€ {df_f['Importo'].sum():,.2f}")
    
    # 1. Grafico a Torta
    df_pie = df_f.groupby('Categoria')['Importo'].sum().reset_index()
    st.plotly_chart(px.pie(df_pie, values='Importo', names='Categoria', hole=0.5, 
                           title="Suddivisione per Categoria", color='Categoria', color_discrete_map=color_map), use_container_width=True)
    
    # 2. Grafico a Barre Impilate (Stacked)
    mesi_nomi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    df_m = df_f.copy()
    df_m['Mese'] = df_m['Data'].dt.month
    
    # Raggruppiamo per mese e categoria per creare l'effetto "uno sopra l'altro"
    res_m = df_m.groupby(['Mese', 'Categoria'])['Importo'].sum().reset_index()
    
    fig_bar = px.bar(res_m, x='Mese', y='Importo', color='Categoria',
                     title=f"Andamento Mensile Impilato {anno_sel}",
                     color_discrete_map=color_map,
                     category_orders={"Mese": list(range(1, 13))}) # Forza l'ordine dei mesi
    
    fig_bar.update_layout(
        xaxis=dict(tickmode='array', tickvals=list(range(1, 13)), ticktext=mesi_nomi),
        barmode='stack', # <--- Cruciale: mette i colori uno sopra l'altro
        xaxis_title="Mesi dell'anno",
        yaxis_title="Totale Speso (€)",
        legend_title="Categorie"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Storico e Eliminazione
    st.subheader("📜 Ultime voci")
    df_mini = df_f[['Data', 'Categoria', 'Descrizione', 'Importo']].copy().sort_values("Data", ascending=False)
    df_mini['Data'] = df_mini['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_mini, use_container_width=True, hide_index=True)
    
    with st.expander("🗑️ Elimina una voce"):
        idx_del = st.selectbox("Seleziona spesa", df_f.index, 
                               format_func=lambda x: f"{df.loc[x,'Data'].strftime('%d/%m')} - {df.loc[x,'Descrizione']} (€{df.loc[x,'Importo']})")
        if st.button("ELIMINA", use_container_width=True):
            df = df.drop(idx_del); df.to_csv(DATA_FILE, index=False); st.rerun()
else:
    st.info("Nessun dato trovato.")

# Configurazione Modelli
st.divider()
with st.expander("⚙️ CONFIGURA MODELLI"):
    with st.form("f_mod"):
        c1 = st.selectbox("Categoria", cat_lista_clean)
        c2 = st.text_input("Nome Modello")
        c3 = st.number_input("Importo", min_value=0.0)
        if st.form_submit_button("CREA", use_container_width=True):
            nuovo_m = pd.DataFrame([[c1, c2, c3, "Mensile", date.today()]], columns=["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True); df_rec.to_csv(RECURRING_FILE, index=False); st.rerun()
