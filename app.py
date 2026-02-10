import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

# --------------------------------------------------
# CONFIG STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="Doji + Earnings Screener (Italia)",
    layout="wide"
)

st.title("📊 Screener Doji + Earnings – Italia")
st.write(
    "Screening di azioni italiane con **pseudo-doji ieri** "
    "e **comunicazione utili oggi**.\n\n"
    "⚠️ Logica adattata a dati reali Yahoo (es. RACE.MI)."
)

# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.header("📎 Input")

uploaded_file = st.sidebar.file_uploader(
    "Carica file .txt con ticker (uno per riga)",
    type=["txt"]
)

show_debug = st.sidebar.checkbox("Mostra DEBUG doji", value=True)

# --------------------------------------------------
# FUNZIONE DOJI (PSEUDO-DOJI REALISTICA)
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

    # ❌ non è nemmeno pseudo-doji
    if body_pct > 0.30:
        return None, (body_pct, upper_pct, lower_pct)

    # 🟢 Dragonfly / pseudo-dragonfly (RACE style)
    if lower > upper * 1.3 and body <= lower * 0.6:
        return "Dragonfly / Pseudo-Doji", (body_pct, upper_pct, lower_pct)

    # 🔴 Gravestone
    if upper > lower * 1.3 and body <= upper * 0.6:
        return "Gravestone / Pseudo-Doji", (body_pct, upper_pct, lower_pct)

    # ⚪ Doji generica / indecisione
    return "Pseudo-Doji", (body_pct, upper_pct, lower_pct)

# --------------------------------------------------
# LETTURA TICKER
# --------------------------------------------------
if not uploaded_file:
    st.warning("⬅️ Carica un file .txt con i ticker")
    st.stop()

tickers = uploaded_file.read().decode("utf-8").splitlines()
tickers = [t.strip().upper() for t in tickers if t.strip()]

# --------------------------------------------------
# SCREENING
# --------------------------------------------------
results = []
debug_rows = []

with st.spinner("🔍 Screening in corso..."):
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            # --- PREZZI ---
            df = stock.history(period="10d", interval="1d")
            if df.empty:
                continue

            # ultima candela CHIUSA (robusta per EU / fuso)
            last_closed = df[df.index.date < date.today()]
            if last_closed.empty:
                continue

            candle = last_closed.iloc[-1]

            doji_type, metrics = classify_doji(candle)
            if metrics:
                body_pct, upper_pct, lower_pct = metrics
            else:
                body_pct = upper_pct = lower_pct = None

            if not doji_type:
                continue

            # --- EARNINGS ---
            cal = stock.calendar
            if cal.empty or "Earnings Date" not in cal.index:
                continue

            earnings_date = cal.loc["Earnings Date"][0].date()
            if earnings_date != date.today():
                continue

            # --- TradingView link ---
            tv_symbol = ticker.replace(".MI", "")
            tv_link =_
