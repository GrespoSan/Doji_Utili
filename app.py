import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

# Configurazione Pagina
st.set_page_config(page_title="Doji Scanner Pro", layout="wide")

st.title("🔍 Scanner Doji (Solo Sessione Conclusa)")
st.write("Analisi accurata della candela di ieri, ignorando la sessione in corso.")

# --- Funzione Identificazione Doji ---
def is_doji(open_p, high, low, close, threshold=0.1):
    # Usiamo float() per essere sicuri di non passare Series a causa di bug di yfinance
    o, h, l, c = float(open_p), float(high), float(low), float(close)
    body = abs(o - c)
    total_range = h - l
    if total_range == 0: return False
    return body <= (total_range * threshold)

# --- Caricamento File ---
uploaded_file = st.file_uploader("Carica file .txt con i ticker (es. ENI.MI)", type="txt")

if uploaded_file is not None:
    # Pulizia lista ticker
    tickers = [line.decode("utf-8").strip().upper() for line in uploaded_file if line.strip()]
    
    if st.button("Avvia Analisi"):
        results = []
        progress_bar = st.progress(0)
        today = date.today()

        for i, t_symbol in enumerate(tickers):
            try:
                # Usiamo Ticker.history che è più affidabile per ticker singoli
                ticker_obj = yf.Ticker(t_symbol)
                df = ticker_obj.history(period="7d", interval="1d")
                
                if not df.empty and len(df) >= 2:
                    # Rimuoviamo eventuali multi-index o colonne extra
                    df = df[['Open', 'High', 'Low', 'Close']]
                    
                    # Identifichiamo la candela di ieri
                    last_row_date = df.index[-1].date()
                    if last_row_date == today:
                        target_candle = df.iloc[-2]
                    else:
                        target_candle = df.iloc[-1]
                    
                    o, h, l, c = target_candle['Open'], target_candle['High'], target_candle['Low'], target_candle['Close']
                    
                    if is_doji(o, h, l, c):
                        results.append({
                            "Ticker": t_symbol,
                            "Data": target_candle.name.strftime('%Y-%m-%d'),
                            "Open": round(float(o), 3),
                            "High": round(float(h), 3),
                            "Low": round(float(l), 3),
                            "Close": round(float(c), 3),
                            "Corpo %": f"{round((abs(o-c)/(h-l if h-l !=0 else 1))*100, 2)}%"
                        })
            except Exception as e:
                # Questo logga l'errore specifico ma permette allo script di continuare
                st.error(f"Impossibile analizzare {t_symbol}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(tickers))

        # --- Visualizzazione Risultati ---
        if results:
            st.success(f"Analisi completata! Trovate {len(results)} potenziali Doji.")
            df_final = pd.DataFrame(results)
            st.dataframe(df_final, use_container_width=True)
        else:
            st.warning("Nessuna Doji trovata nella sessione di ieri per la lista fornita.")