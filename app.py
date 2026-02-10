import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Configurazione
st.set_page_config(page_title="Doji Scanner Pro", layout="wide")

st.title("🎯 Doji Scanner - Analisi 'Ieri'")
st.markdown("""
Questo strumento analizza la **candela precedente a quella di oggi**. 
* Se oggi il mercato è aperto, ignora la candela in movimento e guarda quella di ieri.
* Usa lo **slider** qui sotto per allargare la ricerca se non trovi risultati.
""")

# --- Sidebar per Parametri ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    # Aumentiamo il default a 0.20 (20%) per catturare anche le "Spinning Top" come quella di RACE
    threshold = st.slider("Tolleranza Doji (Ratio Corpo/Range)", 
                          min_value=0.01, 
                          max_value=0.50, 
                          value=0.20, 
                          step=0.01,
                          help="0.1 = Molto severo (Doji perfetta). 0.3 = Più permissivo (include Spinning Tops).")
    
    st.info(f"Cercando candele con corpo inferiore al {int(threshold*100)}% del range.")

# --- Funzione Logica ---
def analyze_ticker(ticker_symbol, threshold):
    try:
        # Scarichiamo dati recenti
        ticker = yf.Ticker(ticker_symbol)
        # Scarichiamo 5 giorni per avere margine sui weekend
        df = ticker.history(period="5d", interval="1d")
        
        if df.empty or len(df) < 2:
            return None, "Dati insufficienti"

        # Gestione date per prendere SEMPRE la penultima candela se l'ultima è oggi
        last_date = df.index[-1].date()
        today_date = datetime.now().date()
        
        # Logica di selezione riga
        if last_date == today_date:
            # Mercato aperto o dati di oggi presenti: prendiamo la PENULTIMA riga (ieri)
            target_row = df.iloc[-2]
            target_date = df.index[-2].date()
        else:
            # Dati fermi a ieri/venerdì: prendiamo l'ULTIMA riga
            target_row = df.iloc[-1]
            target_date = last_date

        # Estrazione Valori
        o = float(target_row['Open'])
        h = float(target_row['High'])
        l = float(target_row['Low'])
        c = float(target_row['Close'])
        
        # Calcoli Doji
        body = abs(c - o)
        total_range = h - l
        
        # Evitiamo divisione per zero
        if total_range == 0:
            ratio = 0
        else:
            ratio = body / total_range
            
        is_doji = ratio <= threshold

        return {
            "Ticker": ticker_symbol,
            "Data Candela": target_date,
            "Open": round(o, 2),
            "Close": round(c, 2),
            "High": round(h, 2),
            "Low": round(l, 2),
            "Body": round(body, 3),
            "Range": round(total_range, 3),
            "Ratio": round(ratio, 4), # Questo è il numero chiave
            "Is Doji": "✅ SI" if is_doji else "❌ NO"
        }, None

    except Exception as e:
        return None, str(e)

# --- Interfaccia ---
uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if uploaded_file:
    tickers = [line.decode("utf-8").strip().upper() for line in uploaded_file if line.strip()]
    
    if st.button(f"Analizza {len(tickers)} Ticker"):
        results = []
        debug_log = []
        
        progress_bar = st.progress(0)
        
        for i, t in enumerate(tickers):
            data, error = analyze_ticker(t, threshold)
            
            if data:
                # Salviamo tutto per il debug
                debug_log.append(data)
                # Salviamo nei risultati solo se è Doji
                if data["Is Doji"] == "✅ SI":
                    results.append(data)
            
            progress_bar.progress((i + 1) / len(tickers))
        
        # Mostra Risultati
        st.subheader("🎯 Risultati Trovati")
        if results:
            df_res = pd.DataFrame(results)
            # Mostriamo le colonne più importanti
            st.dataframe(df_res[["Ticker", "Data Candela", "Open", "Close", "Ratio", "Is Doji"]], use_container_width=True)
        else:
            st.warning("Nessuna Doji trovata con questa soglia.")

        # --- SEZIONE DEBUG (Fondamentale per capire perché non trova) ---
        with st.expander("🕵️‍♂️ Visualizza Analisi Completa (Debug)"):
            st.write("Qui vedi i calcoli esatti per TUTTI i ticker caricati. Verifica il valore 'Ratio'.")
            if debug_log:
                st.dataframe(pd.DataFrame(debug_log))