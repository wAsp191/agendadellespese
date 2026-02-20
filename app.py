import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io
from openpyxl.styles import Font

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Pro", layout="wide", page_icon="💰")

DATA_FILE = "spese_casa_v4.csv"
RECURRING_FILE = "modelli_ricorrenti_v4.csv"

# --- FUNZIONE CARICAMENTO DATI ---
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

# Inizializzazione Database
df = load_data(DATA_FILE, ["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
df_rec = load_data(RECURRING_FILE, ["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])

# --- FUNZIONE EXCEL ---
def to_excel_pro(df_to_download):
    output = io.BytesIO()
    df_excel = df_to_download.copy()
    df_excel['Data'] = df_excel['Data'].dt.strftime('%d/%m/%Y')
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Report Spese')
        workbook = writer.book
        worksheet = writer.sheets['Report Spese']
        bold_font = Font(bold=True)
        for cell in worksheet[1]:
            cell.font = bold_font
        last_row = len(df_excel) + 2
        worksheet.cell(row=last_row, column=3, value="TOTALE:")
        worksheet.cell(row=last_row, column=4, value=df_to_download['Importo'].sum())
        worksheet.cell(row=last_row, column=3).font = bold_font
        worksheet.cell(row=last_row, column=4).font = bold_font
        for col in worksheet.columns:
            max_length = max(len(str(cell.value)) for cell in col)
            worksheet.column_dimensions[col[0].column_letter].width = max_length + 2
    return output.getvalue()

# --- INTERFACCIA PRINCIPALE ---
st.title("🏠 Dashboard Spese Casa")

# --- SIDEBAR: FILTRI E EXPORT ---
st.sidebar.header("🔍 Filtri e Report")
anni_disponibili = sorted(df['Data'].dt.year.unique(), reverse=True) if not df.empty else [date.today().year]
anno_selezionato = st.sidebar.selectbox("Seleziona Anno", anni_disponibili)
categorie_lista = ["Tutte", "Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"]
filtro_cat = st.sidebar.selectbox("Filtra per Categoria", categorie_lista)

# Logica di filtraggio
df_filtrato = df[df['Data'].dt.year == anno_selezionato].copy() if not df.empty else pd.DataFrame()
if filtro_cat != "Tutte" and not df_filtrato.empty:
    df_filtrato = df_filtrato[df_filtrato["Categoria"] == filtro_cat]

# Bottone Download Excel
if not df_filtrato.empty:
    st.sidebar.download_button(
        label="📥 Scarica Report Excel",
        data=to_excel_pro(df_filtrato),
        file_name=f"Spese_{anno_selezionato}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- TASTO AGGIUNGI (+) ---
with st.expander("➕ **CLICCA QUI PER AGGIUNGERE UNA SPESA**", expanded=False):
    t1, t2 = st.tabs(["✍️ Inserimento Manuale", "🔁 Usa i tuoi Modelli"])
    
    with t1:
        with st.form("form_manuale", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            d = c1.date_input("Data", date.today())
            cat = c1.selectbox("Categoria", categorie_lista[1:])
            imp = c2.number_input("Importo (€)", min_value=0.0, step=0.01)
            per = c2.text_input("Periodo (es. Gen-Feb)")
            des = c3.text_input("Descrizione")
            if st.form_submit_button("Salva Spesa"):
                nuova = pd.DataFrame([[pd.to_datetime(d), cat, des, imp, per]], columns=df.columns)
                df = pd.concat([df, nuova], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Spesa registrata correttamente!")
                st.rerun()
                
    with t2:
        if df_rec.empty:
            st.warning("Non hai ancora creato modelli. Vai in fondo alla pagina.")
        else:
            for i, row in df_rec.iterrows():
                col_a, col_b = st.columns([3, 1])
                col_a.info(f"**{row['Descrizione']}** - €{row['Importo']} ({row['Cadenza']})")
                if col_b.button("Inserisci ora", key=f"rec_btn_{i}"):
                    nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                    df = pd.concat([df, nuova_s], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.rerun()

# --- VISUALIZZAZIONE DATI ---
if not df_filtrato.empty:
    st.divider()
    # Metrica Totale
    st.metric(f"Totale {filtro_cat}", f"€ {df_filtrato['Importo'].sum():,.2f}")

    # Grafici
    col_l, col_r = st.columns(2)
    with col_l:
        df_pie = df_filtrato.groupby('Categoria')['Importo'].sum().reset_index()
        df_pie['Etichetta'] = df_pie.apply(lambda r: f"{r['Categoria']}: €{r['Importo']:,.2f}", axis=1)
        st.plotly_chart(px.pie(df_pie, values='Importo', names='Etichetta', title="Distribuzione Budget", hole=0.4), use_container_width=True)
    
    with col_r:
        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        df_m = df_filtrato.copy()
        df_m['M_Num'] = df_m['Data'].dt.month
        res = df_m.groupby('M_Num')['Importo'].sum().reindex(range(1, 13), fill_value=0).reset_index()
        res['Mese'] = mesi
        fig_area = px.area(res, x='Mese', y='Importo', title=f"Trend {anno_selezionato}")
        fig_area.update_layout(yaxis_range=[0, max(res['Importo'].max() + 100, 800)])
        st.plotly_chart(fig_area, use_container_width=True)

    # Storico
    st.divider()
    st.subheader("📜 Storico")
    df_disp = df_filtrato.copy().sort_values("Data", ascending=False)
    df_disp['Data'] = df_disp['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_disp, use_container_width=True)
    
    with st.expander("🗑️ Elimina una spesa"):
        idx_to_del = st.selectbox("Seleziona spesa", df_filtrato.index, 
                                  format_func=lambda x: f"{df.loc[x, 'Data'].strftime('%d/%m/%Y')} - {df.loc[x, 'Descrizione']} (€{df.loc[x, 'Importo']})")
        if st.button("Elimina Definitivamente"):
            df = df.drop(idx_to_del)
            df.to_csv(DATA_FILE, index=False)
            st.rerun()
else:
    st.info("Nessuna spesa trovata. Aggiungi la tua prima bolletta dal tasto + qui sopra!")

# --- CONFIGURAZIONE MODELLI ---
st.divider()
with st.expander("⚙️ CONFIGURAZIONE MODELLI RICORRENTI"):
    with st.form("form_modelli"):
        c1, c2, c3, c4 = st.columns(4)
        rcat = c1.selectbox("Categoria", categorie_lista[1:])
        rdes = c2.text_input("Nome Modello (es. Fibra Iliad)")
        rimp = c3.number_input("Importo Standard", min_value=0.0)
        rcad = c4.selectbox("Cadenza", ["Mensile", "Bimestrale", "Annuale"])
        if st.form_submit_button("Crea Modello"):
            nuovo_m = pd.DataFrame([[rcat, rdes, rimp, rcad, date.today()]], columns=["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
            df_rec.to_csv(RECURRING_FILE, index=False)
            st.rerun()
