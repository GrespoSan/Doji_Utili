import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

st.set_page_config(page_title="Doji + Earnings Screener", layout="wide")

st.title("📊 Screener Doji + Earnings (Italia)")
st.write("Azioni con **doji ieri** e **earnings oggi**, con link TradingView")

# -------------------------
# PARAMETRI
# -------------------------
doji_threshold = st.slider("Soglia corpo doji (% del range)", 1, 20, 10) / 100
shadow_ratio = st.slider("Rapporto ombra lunga / range", 30, 90, 60) / 100

uploaded_file = st.file_uploader("📎 Carica file .txt con ticker", type=["txt"])

# -------------------------
# FUNZIONI DOJI
# -------------------------
def classify_doji(row):
    o, c, h, l = row["Open"], row["Close"], row["High"], row["Low"]
    body = abs(c - o)
    rng = h - l

    if rng == 0:
        return None

    upper = h - max(o, c)
    lower = min(o, c) - l

    if body > rng * doji_threshold:
        return None

    # Dragonfly
    if lower > rng * shadow_ratio and upper < rng * 0.1:
        return "Dragonfly Doji"

    # Gravestone
    if upper > rng * shadow_ratio and lower < rng * 0.1:
        return "Gravestone Doji"

    return "Doji"

# -------------------------
# LETTURA TICKER
# -------------------------
tickers = []

if uploaded_file:
    tickers = uploaded_file.read().decode("utf-8").splitlines()
    tickers = [t.strip().upper() for t in tickers if t.strip()]

if not tickers:
    st.warning("Carica un file .txt con i ticker.")
    st.stop()

# -------------------------
# SCREENING
# -------------------------
results = []

with st.spinner("🔍 Analisi in corso..."):
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="5d")

            if len(df) < 2:
                continue

            yesterday = df.iloc[-2]
            doji_type = classify_doji(yesterday)

            if not doji_type:
                continue

            cal = stock.calendar
            if cal.empty:
                continue

            earnings_date = cal.loc["Earnings Date"][0].date()

            if earnings_date != date.today():
                continue

            tv_link = f"https://www.tradingview.com/chart/?symbol=BIST:{ticker.replace('.MI','')}"

            results.append({
                "Ticker": ticker,
                "Doji Type": doji_type,
                "Earnings Date": earnings_date,
                "TradingView": tv_link
            })

        except Exception:
            continue

# -------------------------
# OUTPUT
# -------------------------
if results:
    df_res = pd.DataFrame(results)

    st.success(f"✅ Trovati {len(df_res)} titoli")

    st.dataframe(
        df_res,
        use_container_width=True,
        column_config={
            "TradingView": st.column_config.LinkColumn("TradingView")
        }
    )
else:
    st.info("Nessun titolo trovato oggi.")
