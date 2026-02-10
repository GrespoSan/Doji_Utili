import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Scanner Doji Real-Time", layout="wide")

st.title("🎯 Scanner Doji Real-Time & Earnings")
st.markdown("""
Analisi della candela di **oggi** (anche se il mercato è ancora aperto).
* Tutti i titoli Doji verranno mostrati.
* Quelli con Earnings domani saranno evidenziati.
""")

with st.sidebar:
    st.header("⚙️ Parametri")
    threshold = st.slider("Tolleranza Doji (Corpo/Range)", 
                          min_value=0.01, max_value=0.50, value=0.20, step=0.01)
    st.info("Suggerimento: Se mancano 15 min alla chiusura, la Doji che vedi ora è molto probabile che sia quella definitiva.")

def get_data_and_check_earnings(ticker_symbol, threshold):
    try:
        t_obj = yf.Ticker(ticker_symbol)
        # Scarichiamo i dati intraday/daily più recenti
        df = t_obj.history(period="2d", interval="1d")
        
        if df.empty:
            return None
            
        # Prendiamo l'ultima riga (quella di oggi in corso)
        today_row = df.iloc[-1]
        o, h, l, c = float(today_row['Open']), float(today_row['High']), float(today_row['Low']), float(today_row['Close'])
        
        body = abs(c - o)
        total_range = h - l
        ratio = body / total_range if total_range != 0 else 0
        
        # 1. Verifica Doji
        is_doji = ratio <= threshold
        
        if not is_doji:
            return None # Saltiamo se non è Doji

        # 2. Verifica Earnings Domani
        is_earnings_tomorrow = False
        tomorrow = date.today() + timedelta(days=1)
        try:
            cal = t_obj.calendar
            if cal and 'Earnings Date' in cal:
                is_earnings_tomorrow = any(d.date() == tomorrow for d in cal['Earnings Date'] if hasattr(d, 'date'))
        except:
            pass

        return {
            "Ticker": ticker_symbol,
            "Prezzo": round(c, 2),
            "Ratio Corpo": round(ratio, 4),
            "Earnings Domani": "🔥 SÌ" if is_earnings_tomorrow else "No",
            "Data": df.index[-1].strftime('%Y-%m-%d')
        }
    except:
        return None

uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if uploaded_file:
    content = uploaded_file.getvalue().decode("utf-8")
    clean_content = content.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    tickers = [t.strip().upper() for t in clean_content.split(' ') if t.strip()]
    
    if st.button("Scansiona Mercato"):
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(tickers):
            res = get_data_and_check_earnings(t, threshold)
            if res:
                results.append(res)
            progress_bar.progress((i + 1) / len(tickers))
        
        if results:
            df_final = pd.DataFrame(results)
            # Ordiniamo: prima quelli con Earnings, poi per Ratio Doji
            df_final = df_final.sort_values(by=["Earnings Domani", "Ratio Corpo"], ascending=[False, True])
            
            st.success(f"Trovate {len(results)} Doji in formazione!")
            
            # Formattazione per evidenziare le righe con Earnings
            def highlight_earnings(s):
                return ['background-color: #2e7d32' if s['Earnings Domani'] == "🔥 SÌ" else '' for _ in s]
            
            st.dataframe(df_final.style.apply(highlight_earnings, axis=1), use_container_width=True)
        else:
            st.warning("Nessuna Doji rilevata al momento.")