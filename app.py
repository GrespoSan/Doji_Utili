import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

# Configurazione Pagina
st.set_page_config(page_title="Doji Scanner - Yesterday Only", layout="wide")

st.title("📊 Scanner Doji: Sessione Precedente")
st.write("Il sistema analizzerà solo la candela dell'ultima giornata di contrattazione conclusa.")

# --- Funzione Identificazione Doji ---
def is_doji(open_p, high, low, close, threshold=0.1):
    body = abs(open_p - close)
    total_range = high - low
    if total_range == 0: return False
    return body <= (total_range * threshold)

# --- Caricamento File ---
uploaded_file = st.file_uploader("Carica file .txt con i ticker", type="txt")

if uploaded_file is not None:
    tickers = [line.decode("utf-8").strip().upper() for line in uploaded_file]
    
    if st.button("Analizza Candele di Ieri"):
        results = []
        progress_bar = st.progress(0)
        today = date.today()

        for i, ticker in enumerate(tickers):
            try:
                # Scarichiamo gli ultimi 7 giorni per coprire i weekend
                df = yf.download(ticker, period="7d", interval="1d", progress=False)
                
                if not df.empty and len(df) >= 2:
                    # Controlliamo se l'ultima riga è 'oggi'
                    last_row_date = df.index[-1].date()
                    
                    if last_row_date == today:
                        # Se l'ultima è oggi, prendiamo la penultima (ieri)
                        target_candle = df.iloc[-2]
                    else:
                        # Se l'ultima non è oggi (es. è sabato), l'ultima è quella valida
                        target_candle = df.iloc[-1]
                    
                    o, h, l, c = target_candle['Open'], target_candle['High'], target_candle['Low'], target_candle['Close']
                    
                    if is_doji(o, h, l, c):
                        results.append({
                            "Ticker": ticker,
                            "Data Analizzata": target_candle.name.strftime('%Y-%m-%d'),
                            "Open": round(float(o), 4),
                            "High": round(float(h), 4),
                            "Low": round(float(l), 4),
                            "Close": round(float(c), 4),
                            "Corpo %": f"{round((abs(o-c)/(h-l if h-l !=0 else 1))*100, 2)}%"
                        })
            except Exception as e:
                st.error(f"Errore su {ticker}: {e}")
            
            progress_bar.progress((i + 1) / len(tickers))

        # --- Visualizzazione ---
        if results:
            st.success(f"Trovate {len(results)} candele simili a Doji per l'ultima sessione conclusa.")
            st.dataframe(pd.DataFrame(results), use_container_width=True)
        else:
            st.info("Nessuna Doji trovata per i ticker selezionati.")