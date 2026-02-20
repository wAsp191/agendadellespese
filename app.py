import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io
from openpyxl.styles import Font # <--- Nuova importazione necessaria

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Pro", layout="wide", page_icon="💰")

DATA_FILE = "spese_casa_v4.csv"
RECURRING_FILE = "modelli_ricorrenti_v4.csv"

# --- FUNZIONE CARICAMENTO ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df_loaded = pd.read_csv(file)
            if not df_loaded.empty:
                df_loaded['Data'] = pd.to_datetime(df_loaded['Data'], errors='coerce')
                df_loaded = df_loaded.dropna(subset=['Data'])
            return df_loaded
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

df = load_data(DATA_FILE, ["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
df_rec = load_data(RECURRING_FILE, ["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])

# --- FUNZIONE EXCEL AGGIORNATA ---
def to_excel_pro(df_to_download):
    output = io.BytesIO()
    df_excel = df_to_download.copy()
    
    # Formattazione data per Excel
    df_excel['Data'] = df_excel['Data'].dt.strftime('%d/%m/%Y')
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Report Spese')
        
        workbook = writer.book
        worksheet = writer.sheets['Report Spese']
        
        # 1. Stile Grassetto per Intestazioni
        bold_font = Font(bold=True)
        for cell in worksheet[1]:
            cell.font = bold_font
            
        # 2. Aggiunta riga Totale in fondo
        last_row = len(df_excel) + 2
        worksheet.cell(row=last_row, column=3, value="TOTALE:")
        worksheet.cell(row=last_row, column=4, value=df_to_download['Importo'].sum())
        worksheet.cell(row=last_row, column=3).font = bold_font
        worksheet.cell(row=last_row, column=4).font = bold_font

        # 3. Autofit delle colonne
        for col in worksheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except: pass
            worksheet.column_dimensions[column].width = max_length + 2
            
    return output.getvalue()

# --- INTERFACCIA ---
st.title("🏠 Dashboard Spese Casa")

# Sidebar
st.sidebar.header("🔍 Filtri e Report")
anni_disponibili = sorted(df['Data'].dt.year.unique(), reverse=True) if not df.empty else [date.today().year]
anno_selezionato = st.sidebar.selectbox("Seleziona Anno", anni_disponibili)
categorie_lista = ["Tutte", "Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"]
filtro_cat = st.sidebar.selectbox("Filtra per Categoria", categorie_lista)

# Filtro dati
df_filtrato = df[df['Data'].dt.year == anno_selezionato].copy() if not df.empty else df.copy()
if filtro_cat != "Tutte":
    df_filtrato = df_filtrato[df_filtrato["Categoria"] == filtro_cat]

# Bottone Download
if not df_filtrato.empty:
    st.sidebar.download_button(
        label="📥 Scarica Excel Professionale",
        data=to_excel_pro(df_filtrato),
        file_name=f"Spese_{anno_selezionato}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- IL RESTO DEL CODICE (Tasto +, Grafici, Modelli) rimane come nella v7 ---
# ... (Inserisci qui le sezioni con gli expander "+" e i grafici plotly)
