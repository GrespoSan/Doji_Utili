import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Doji Today - Earnings Tomorrow", layout="wide")

st.title("🎯 Scanner: Doji Oggi ➔ Earnings Domani")
st.markdown("""
Questo scanner individua i titoli che hanno appena chiuso (o stanno chiudendo) la sessione con una **Doji** e che hanno il rilascio degli **utili previsto per domani**.
""")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Parametri")
    threshold = st.slider("Tolleranza Doji (Corpo/Range)", 
                          min_value=0.01, max_value=0.50, value=0.20, step=0.01)
    
    st.info("Il sistema analizzerà l'ultima candela disponibile (Oggi) e cercherà Earnings per la data di domani.")

# --- Funzione 1: Analisi Doji Oggi ---
def analyze_today_doji(ticker_obj, threshold):
    try:
        # Scarichiamo gli ultimi 3 giorni
        df = ticker_obj.history(period="3d", interval="1d")
        if df.empty:
            return None
            
        # Prendiamo l'ULTIMA candela (Oggi)
        target_row = df.iloc[-1]
        target_date = df.index[-1].date()

        o, h, l, c = float(target_row['Open']), float(target_row['High']), float(target_row['Low']), float(target_row['Close'])
        
        body = abs(c - o)
        total_range = h - l
        
        ratio = body / total_range if total_range != 0 else 0
        is_doji = ratio <= threshold

        return {
            "Data Oggi": target_date,
            "Open": round(o, 2),
            "Close": round(c, 2),
            "Ratio": round(ratio, 4),
            "Is Doji": is_doji
        }
    except:
        return None

# --- Funzione 2: Controllo Earnings Domani ---
def check_earnings_tomorrow(ticker_obj):
    try:
        cal = ticker_obj.calendar
        if cal and 'Earnings Date' in cal:
            tomorrow = date.today() + timedelta(days=1)
            # Verifichiamo se domani è presente nella lista delle date utili
            return any(d.date() == tomorrow for d in cal['Earnings Date'] if hasattr(d, 'date'))
        return False
    except:
        return False

# --- Main ---
uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    clean_content = content.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    tickers = [t.strip().upper() for t in clean_content.split(' ') if t.strip()]
    
    if st.button("Avvia Scansione Predittiva"):
        results = []
        progress_bar = st.progress(0)
        
        for i, t_symbol in enumerate(tickers):
            t_obj = yf.Ticker(t_symbol)
            
            # 1. Vediamo se oggi è una Doji
            pattern = analyze_today_doji(t_obj, threshold)
            
            if pattern and pattern['Is Doji']:
                # 2. Se è Doji, controlliamo se domani ci sono gli utili
                if check_earnings_tomorrow(t_obj):
                    pattern['Ticker'] = t_symbol
                    pattern['Earnings Domani'] = (date.today() + timedelta(days=1)).strftime('%Y-%m-%d')
                    results.append(pattern)
            
            progress_bar.progress((i + 1) / len(tickers))
        
        if results:
            st.success(f"Trovati {len(results)} titoli con setup esplosivo!")
            st.dataframe(pd.DataFrame(results)[["Ticker", "Data Oggi", "Earnings Domani", "Ratio"]], use_container_width=True)
            st.balloons()
        else:
            st.warning("Nessun titolo corrisponde ai criteri (Doji oggi + Earnings domani).")