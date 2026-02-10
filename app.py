import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Scanner & Chart Doji", layout="wide")

st.title("🎯 Doji Explorer: Scanner + Analisi Grafica")
st.markdown("Analizza le Doji in formazione e visualizza il grafico tecnico istantaneamente.")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Parametri")
    threshold = st.slider("Tolleranza Doji (Corpo/Range)", 
                          min_value=0.01, max_value=0.50, value=0.20, step=0.01)
    st.info("Dopo la scansione, apparirà un menu per selezionare il grafico del titolo desiderato.")

# --- Funzioni di Supporto ---
def get_analysis(ticker_symbol, threshold):
    try:
        t_obj = yf.Ticker(ticker_symbol)
        df = t_obj.history(period="1mo", interval="1d") # Prendiamo 1 mese per il grafico
        
        if df.empty or len(df) < 2:
            return None
            
        today_row = df.iloc[-1]
        o, h, l, c = float(today_row['Open']), float(today_row['High']), float(today_row['Low']), float(today_row['Close'])
        
        body = abs(c - o)
        total_range = h - l
        ratio = body / total_range if total_range != 0 else 0
        
        if ratio <= threshold:
            # Controllo Earnings Domani
            is_earnings_tomorrow = False
            tomorrow = date.today() + timedelta(days=1)
            try:
                cal = t_obj.calendar
                if cal and 'Earnings Date' in cal:
                    is_earnings_tomorrow = any(d.date() == tomorrow for d in cal['Earnings Date'] if hasattr(d, 'date'))
            except: pass

            return {
                "Ticker": ticker_symbol,
                "Prezzo": round(c, 2),
                "Ratio": round(ratio, 4),
                "Earnings Domani": "🔥 SÌ" if is_earnings_tomorrow else "No",
                "df": df # Passiamo il dataframe per il grafico
            }
        return None
    except:
        return None

# --- Main Logic ---
uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    clean_content = content.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    tickers = [t.strip().upper() for t in clean_content.split(' ') if t.strip()]
    
    if st.button("Avvia Scansione"):
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(tickers):
            res = get_analysis(t, threshold)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(tickers))
        
        # Salviamo i risultati nello stato della sessione per non perderli al cambio selezione
        st.session_state['results'] = results

    # --- Visualizzazione Risultati e Grafico ---
    if 'results' in st.session_state and st.session_state['results']:
        res_list = st.session_state['results']
        df_display = pd.DataFrame(res_list).drop(columns=['df'])
        
        st.subheader(f"Trovate {len(res_list)} Doji")
        st.dataframe(df_display, use_container_width=True)

        st.divider()

        # --- SELEZIONE TITOLO PER GRAFICO ---
        st.subheader("📈 Analisi Dettagliata Grafico")
        ticker_to_show = st.selectbox("Seleziona un ticker per vedere il grafico:", [r['Ticker'] for r in res_list])
        
        # Recuperiamo i dati storici del ticker selezionato
        selected_data = next(item for item in res_list if item["Ticker"] == ticker_to_show)
        df_chart = selected_data['df']

        # Creazione Grafico Candlestick con Plotly
        fig = go.Figure(data=[go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'],
            high=df_chart['High'],
            low=df_chart['Low'],
            close=df_chart['Close'],
            name="Prezzo"
        )])

        fig.update_layout(
            title=f"Grafico Daily - {ticker_to_show} (Doji Ratio: {selected_data['Ratio']})",
            yaxis_title="Prezzo",
            xaxis_title="Data",
            template="plotly_dark",
            xaxis_rangeslider_visible=False,
            height=600
        )

        st.plotly_chart(fig, use_container_width=True)
    elif 'results' in st.session_state:
        st.warning("Nessuna Doji trovata con i parametri attuali.")