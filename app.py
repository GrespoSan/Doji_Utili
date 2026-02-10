import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configurazione Pagina
st.set_page_config(page_title="Doji Scanner Pro", layout="wide")

st.title("🎯 Doji Scanner - Analisi 'Ieri'")
st.markdown("""
Questo strumento analizza la **candela precedente a quella di oggi**. 
* **Supporta liste separate da virgola, spazi o accapo.**
* Usa lo **slider** laterale per regolare la sensibilità (consigliato 0.20 per titoli come RACE).
""")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    threshold = st.slider("Tolleranza Doji (Ratio Corpo/Range)", 
                          min_value=0.01, max_value=0.50, value=0.20, step=0.01,
                          help="0.1 = Doji stretta. 0.3 = Spinning Top.")
    st.write(f"Soglia attuale: **{int(threshold*100)}%**")

# --- Funzione Analisi ---
def analyze_ticker(ticker_symbol, threshold):
    try:
        # Scarica dati (5 giorni per sicurezza weekend)
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d", interval="1d")
        
        if df.empty or len(df) < 2:
            return None
            
        # Logica Selezione Data (Ieri vs Oggi)
        last_date = df.index[-1].date()
        today_date = datetime.now().date()
        
        # Se l'ultima candela è di OGGI, prendiamo la PENULTIMA (Ieri)
        if last_date == today_date:
            target_row = df.iloc[-2]
            target_date = df.index[-2].date()
        else:
            # Se l'ultima è vecchia (es. ieri sera o venerdì), prendiamo l'ULTIMA
            target_row = df.iloc[-1]
            target_date = last_date

        # Dati Numerici
        o = float(target_row['Open'])
        h = float(target_row['High'])
        l = float(target_row['Low'])
        c = float(target_row['Close'])
        
        body = abs(c - o)
        total_range = h - l
        
        if total_range == 0: 
            ratio = 0
        else:
            ratio = body / total_range
            
        is_doji = ratio <= threshold

        return {
            "Ticker": ticker_symbol,
            "Data Candela": target_date,
            "Open": round(o, 3),
            "Close": round(c, 3),
            "High": round(h, 3),
            "Low": round(l, 3),
            "Ratio": round(ratio, 4),
            "Is Doji": is_doji
        }

    except Exception:
        return None

# --- Caricamento e Pulizia File ---
uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if uploaded_file is not None:
    # 1. Leggiamo tutto il contenuto come stringa
    content = uploaded_file.getvalue().decode("utf-8")
    
    # 2. Sostituiamo le virgole e gli 'a capo' con spazi vuoti
    # Questo trasforma "A2A.MI, ENI.MI" in "A2A.MI  ENI.MI"
    clean_content = content.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    
    # 3. Creiamo la lista dividendo per spazi e rimuovendo vuoti
    tickers = [t.strip().upper() for t in clean_content.split(' ') if t.strip()]
    
    # Mostriamo quanti ne abbiamo trovati
    st.info(f"Ho rilevato **{len(tickers)}** ticker nel file.")
    
    if len(tickers) > 0 and st.button("Avvia Analisi"):
        results = []
        progress_bar = st.progress(0)
        
        for i, t in enumerate(tickers):
            data = analyze_ticker(t, threshold)
            if data and data['Is Doji']:
                results.append(data)
            
            progress_bar.progress((i + 1) / len(tickers))
        
        # Risultati
        if results:
            st.success(f"Trovate {len(results)} candele interessanti!")
            df_res = pd.DataFrame(results)
            # Ordiniamo per Ratio (più basso è, più è Doji perfetta)
            df_res = df_res.sort_values(by="Ratio")
            st.dataframe(df_res[["Ticker", "Data Candela", "Open", "Close", "Ratio"]], use_container_width=True)
        else:
            st.warning("Nessuna Doji trovata. Prova ad aumentare la tolleranza nello slider a sinistra.")