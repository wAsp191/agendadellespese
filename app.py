import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import date
import io

# Configurazione Pagina
st.set_page_config(page_title="Home Budget Pro", layout="wide", page_icon="💰")

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
        except Exception:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

# Inizializzazione
df = load_data(DATA_FILE, ["Data", "Categoria", "Descrizione", "Importo", "Periodo"])
df_rec = load_data(RECURRING_FILE, ["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])

st.title("🏠 Dashboard Spese Casa")

# --- SIDEBAR ---
st.sidebar.header("🔍 Filtri e Report")
anni_disponibili = sorted(df['Data'].dt.year.unique(), reverse=True) if not df.empty else [date.today().year]
anno_selezionato = st.sidebar.selectbox("Seleziona Anno", anni_disponibili)
categorie_lista = ["Tutte", "Luce", "Gas", "Acqua", "TARI", "Internet", "Alimentari", "Manutenzione", "Altro"]
filtro_cat = st.sidebar.selectbox("Filtra per Categoria", categorie_lista)

df_filtrato = df[df['Data'].dt.year == anno_selezionato].copy() if not df.empty else df.copy()
if filtro_cat != "Tutte":
    df_filtrato = df_filtrato[df_filtrato["Categoria"] == filtro_cat]

# --- FUNZIONE EXCEL AVANZATA ---
def to_excel_pro(df_to_download):
    output = io.BytesIO()
    df_excel = df_to_download.copy()
    df_excel['Data'] = df_excel['Data'].dt.strftime('%d/%m/%Y')
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_excel.to_excel(writer, index=False, sheet_name='Report Spese')
        # Accesso al foglio per formattazione
        workbook = writer.book
        worksheet = writer.sheets['Report Spese']
        # Rendiamo le intestazioni in grassetto
        for cell in worksheet[1]:
            cell.font = pd.io.formats.excel.ExcelFormatter.header_style['font'] # Semplificato per compatibilità
        # Autofit delle colonne
        for col in worksheet.columns:
            max_length = max(len(str(cell.value)) for cell in col)
            worksheet.column_dimensions[col[0].column_letter].width = max_length + 2
            
    return output.getvalue()

if not df_filtrato.empty:
    st.sidebar.download_button(
        label="📥 Scarica Excel Professionale",
        data=to_excel_pro(df_filtrato),
        file_name=f"Spese_{anno_selezionato}_{filtro_cat}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# --- AGGIUNGI SPESA (+) ---
with st.expander("➕ **CLICCA QUI PER AGGIUNGERE UNA SPESA**", expanded=False):
    t1, t2 = st.tabs(["✍️ Inserimento Manuale", "🔁 Usa i tuoi Modelli"])
    
    with t1:
        with st.form("manual"):
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
                st.success("Salvato!")
                st.rerun()
                
    with t2:
        if df_rec.empty:
            st.warning("Non hai ancora creato modelli. Vai in fondo alla pagina su 'Configurazione Modelli'.")
        else:
            st.write("Clicca su 'Inserisci' per aggiungere la spesa con la data di oggi:")
            for i, row in df_rec.iterrows():
                col_a, col_b = st.columns([3, 1])
                col_a.info(f"**{row['Descrizione']}** - €{row['Importo']} ({row['Cadenza']})")
                if col_b.button("Inserisci", key=f"btn_rec_{i}"):
                    nuova_s = pd.DataFrame([[pd.to_datetime(date.today()), row['Categoria'], row['Descrizione'], row['Importo'], "Ricorrente"]], columns=df.columns)
                    df = pd.concat([df, nuova_s], ignore_index=True)
                    df.to_csv(DATA_FILE, index=False)
                    st.rerun()

# --- DASHBOARD ---
if not df_filtrato.empty:
    st.divider()
    # Grafici (Invariati per brevità, ma ora leggono i totali corretti)
    df_pie = df_filtrato.groupby('Categoria')['Importo'].sum().reset_index()
    df_pie['Etichetta'] = df_pie.apply(lambda r: f"{r['Categoria']}: €{r['Importo']:,.2f}", axis=1)
    
    col_l, col_r = st.columns(2)
    with col_l:
        st.plotly_chart(px.pie(df_pie, values='Importo', names='Etichetta', title="Budget Annuale", hole=0.4), use_container_width=True)
    with col_r:
        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        df_m = df_filtrato.copy()
        df_m['M_Num'] = df_m['Data'].dt.month
        res = df_m.groupby('M_Num')['Importo'].sum().reindex(range(1, 13), fill_value=0).reset_index()
        res['Mese'] = mesi
        fig = px.area(res, x='Mese', y='Importo', title=f"Trend {anno_selezionato}")
        fig.update_layout(yaxis_range=[0, max(res['Importo'].max() + 100, 800)])
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("📜 Storico")
    df_disp = df_filtrato.copy().sort_values("Data", ascending=False)
    df_disp['Data'] = df_disp['Data'].dt.strftime('%d/%m/%Y')
    st.dataframe(df_disp, use_container_width=True)
else:
    st.info("Benvenuto! Crea un modello in fondo o aggiungi una spesa dal tasto +")

# --- MODELLI (IN FONDO) ---
st.divider()
with st.expander("⚙️ CONFIGURAZIONE MODELLI RICORRENTI"):
    st.write("Qui crei i tuoi 'modelli' (es. Netflix, Bolletta Media Acqua). Una volta creati, appariranno nel menù '+' in alto.")
    with st.form("new_mod"):
        c1, c2, c3, c4 = st.columns(4)
        rcat = c1.selectbox("Categoria", categorie_lista[1:])
        rdes = c2.text_input("Nome Modello (es. Abbonamento Fibra)")
        rimp = c3.number_input("Importo Standard", min_value=0.0)
        rcad = c4.selectbox("Frequenza", ["Mensile", "Bimestrale", "Trimestrale", "Annuale"])
        if st.form_submit_button("Crea Modello"):
            nuovo_m = pd.DataFrame([[rcat, rdes, rimp, rcad, date.today()]], 
                                   columns=["Categoria", "Descrizione", "Importo", "Cadenza", "Data"])
            df_rec = pd.concat([df_rec, nuovo_m], ignore_index=True)
            df_rec.to_csv(RECURRING_FILE, index=False)
            st.success("Modello creato! Ora lo trovi nel menù '+' in alto.")
            st.rerun()
