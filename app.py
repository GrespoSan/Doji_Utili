import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, date

# Configurazione Pagina
st.set_page_config(page_title="Doji & Earnings Scanner", layout="wide")

st.title("🎯 Doji Scanner + Earnings Oggi")
st.markdown("""
Questo strumento cerca candele di indecisione (Doji) nella sessione di **ieri**.
* **Filtro Earnings:** Se attivato, mostra solo le aziende che rilasciano gli utili **OGGI**.
""")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Impostazioni Grafiche")
    threshold = st.slider("Tolleranza Doji (Ratio Corpo/Range)", 
                          min_value=0.01, max_value=0.50, value=0.20, step=0.01)
    
    st.divider()
    st.header("💰 Filtro Utili")
    filter_earnings = st.checkbox("Mostra SOLO chi ha gli Earnings OGGI", value=True)

# --- Funzione 1: Analisi Grafica (Doji) ---
def analyze_ticker_pattern(ticker_obj, threshold):
    try:
        # Scarica dati (5 giorni per sicurezza)
        df = ticker_obj.history(period="5d", interval="1d")
        
        if df.empty or len(df) < 2:
            return None
            
        # Logica Selezione Data (Ieri vs Oggi)
        last_date = df.index[-1].date()
        today_date = datetime.now().date()
        
        if last_date == today_date:
            target_row = df.iloc[-2] # Ieri
            target_date = df.index[-2].date()
        else:
            target_row = df.iloc[-1] # Ultima disponibile
            target_date = last_date

        # Calcoli Candela
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
            "Data Candela": target_date,
            "Open": round(o, 3),
            "Close": round(c, 3),
            "Ratio": round(ratio, 4),
            "Is Doji": is_doji
        }

    except Exception:
        return None

# --- Funzione 2: Controllo Earnings (Nuova) ---
def check_earnings_today(ticker_obj):
    try:
        # Recupera il calendario
        cal = ticker_obj.calendar
        
        # yfinance restituisce un dizionario. Cerchiamo la chiave 'Earnings Date'
        # o 'Earnings High' / 'Earnings Low' a seconda della versione.
        # Solitamente 'Earnings Date' contiene una lista di date.
        
        if cal and 'Earnings Date' in cal:
            earnings_dates = cal['Earnings Date']
            today = date.today()
            
            # Controlliamo se una delle date nella lista corrisponde a oggi
            for d in earnings_dates:
                if d == today:
                    return True
        return False
    except Exception:
        return False

# --- Main Script ---
uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if uploaded_file is not None:
    # Parsing file intelligente (virgole, spazi, newlines)
    content = uploaded_file.getvalue().decode("utf-8")
    clean_content = content.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    tickers = [t.strip().upper() for t in clean_content.split(' ') if t.strip()]
    
    st.info(f"Lista caricata: **{len(tickers)}** ticker.")
    
    if len(tickers) > 0 and st.button("Avvia Scansione Completa"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, t_symbol in enumerate(tickers):
            status_text.text(f"Analisi in corso: {t_symbol}...")
            
            # Creiamo l'oggetto Ticker una sola volta
            ticker_obj = yf.Ticker(t_symbol)
            
            # 1. Controllo Grafico (Veloce)
            pattern_data = analyze_ticker_pattern(ticker_obj, threshold)
            
            if pattern_data and pattern_data['Is Doji']:
                # Trovata una Doji!
                
                # 2. Controllo Earnings (Lento - lo facciamo solo se richiesto e se è Doji)
                is_earnings_today = False
                if filter_earnings:
                    is_earnings_today = check_earnings_today(ticker_obj)
                    include_in_results = is_earnings_today
                else:
                    # Se il filtro è spento, includiamo tutto
                    include_in_results = True
                    is_earnings_today = "N/A" # Non controllato

                if include_in_results:
                    pattern_data['Ticker'] = t_symbol
                    pattern_data['Earnings Oggi'] = "✅ SÌ" if is_earnings_today is True else "No/Boh"
                    results.append(pattern_data)
            
            progress_bar.progress((i + 1) / len(tickers))
        
        status_text.text("Scansione completata.")
        
        # Output
        if results:
            st.success(f"Trovati {len(results)} risultati!")
            df_res = pd.DataFrame(results)
            
            # Riordiniamo le colonne per chiarezza
            cols = ["Ticker", "Data Candela", "Earnings Oggi", "Open", "Close", "Ratio"]
            st.dataframe(df_res[cols], use_container_width=True)
        else:
            if filter_earnings:
                st.warning("Nessun ticker trovato che sia SIA una Doji SIA con Earnings oggi.")
            else:
                st.warning("Nessuna Doji trovata.")