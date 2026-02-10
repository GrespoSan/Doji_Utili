import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

# --------------------------------------------------
# CONFIG STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="Doji + Earnings Screener (DEBUG)",
    layout="wide"
)

st.title("📊 Screener Doji – Italia (Debug Avanzato)")
st.write(
    "Mostra tutte le pseudo-doji di ieri anche se gli earnings non sono disponibili su Yahoo.\n"
    "Permette di controllare manualmente le comunicazioni utili."
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.header("📎 Input")
uploaded_file = st.sidebar.file_uploader(
    "Carica file .txt con ticker (uno per riga)", type=["txt"]
)
show_debug = st.sidebar.checkbox("Mostra DEBUG dettagliato", value=True)

if not uploaded_file:
    st.warning("⬅️ Carica un file .txt con i ticker")
    st.stop()

tickers = uploaded_file.read().decode("utf-8").splitlines()
tickers = [t.strip().upper() for t in tickers if t.strip()]

# --------------------------------------------------
# FUNZIONE PSEUDO-DOJI
# --------------------------------------------------
def classify_doji(row):
    o, c, h, l = row["Open"], row["Close"], row["High"], row["Low"]
    body = abs(c - o)
    rng = h - l
    if rng == 0:
        return None, None
    upper = h - max(o, c)
    lower = min(o, c) - l
    body_pct = body / rng
    upper_pct = upper / rng
    lower_pct = lower / rng

    # corpo piccolo massimo 35%
    if body_pct > 0.35:
        return None, (body_pct, upper_pct, lower_pct)

    # Dragonfly / Gravestone meno rigidi
    if lower > upper * 1.1 and body <= lower * 0.7:
        return "Dragonfly / Pseudo-Doji", (body_pct, upper_pct, lower_pct)
    if upper > lower * 1.1 and body <= upper * 0.7:
        return "Gravestone / Pseudo-Doji", (body_pct, upper_pct, lower_pct)

    # Doji generico
    return "Pseudo-Doji", (body_pct, upper_pct, lower_pct)

# --------------------------------------------------
# SCREENING DEBUG
# --------------------------------------------------
results = []
debug_rows = []

with st.spinner("🔍 Screening pseudo-doji in corso..."):
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="10d", interval="1d")
            if df.empty:
                continue

            # Prendi l'ultima candela disponibile
            candle = df.iloc[-2]  # di solito ieri
            doji_type, metrics = classify_doji(candle)
            if not doji_type:
                continue

            body_pct, upper_pct, lower_pct = metrics

            # Earnings (solo se disponibili)
            cal = stock.calendar
            earnings_date = None
            if not cal.empty and "Earnings Date" in cal.index:
                earnings_date = cal.loc["Earnings Date"].iat[0].date()

            # TradingView link
            tv_symbol = ticker.replace(".MI", "")
            tv_link = f"https://www.tradingview.com/chart/?symbol=MIL:{tv_symbol}"

            # Salvataggio risultati
            results.append({
                "Ticker": ticker,
                "Doji Type": doji_type,
                "Candle Date": candle.name.date(),
                "Body %": round(body_pct, 2),
                "Lower Shadow %": round(lower_pct, 2),
                "Upper Shadow %": round(upper_pct, 2),
                "Earnings": earnings_date,
                "TradingView": tv_link
            })

        except Exception as e:
            continue

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------
if results:
    df_res = pd.DataFrame(results)
    st.success(f"✅ Trovate {len(df_res)} pseudo-doji")

    st.dataframe(
        df_res,
        use_container_width=True,
        column_config={
            "TradingView": st.column_config.LinkColumn("TradingView")
        }
    )

    if show_debug:
        st.subheader("🧪 Debug dettagliato")
        st.dataframe(df_res, use_container_width=True)

else:
    st.info("Nessuna pseudo-doji trovata nei ticker caricati.")
