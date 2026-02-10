import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="Doji + Earnings Screener",
    layout="wide"
)

st.title("📊 Screener Doji + Earnings (Italia)")
st.write(
    "Individua azioni italiane che **ieri hanno fatto una doji reale** "
    "e **oggi hanno la comunicazione degli utili**."
)

# --------------------------------------------------
# SIDEBAR PARAMETRI
# --------------------------------------------------
st.sidebar.header("⚙️ Parametri Doji")

max_body_pct = st.sidebar.slider(
    "Corpo massimo (% del range)",
    min_value=5,
    max_value=30,
    value=20
) / 100

dominance_ratio = st.sidebar.slider(
    "Dominanza ombra (x volte)",
    min_value=1.5,
    max_value=4.0,
    value=2.0,
    step=0.1
)

body_shadow_ratio = st.sidebar.slider(
    "Corpo / Ombra dominante",
    min_value=0.2,
    max_value=0.6,
    value=0.35,
    step=0.05
)

uploaded_file = st.sidebar.file_uploader(
    "📎 Carica file .txt con ticker",
    type=["txt"]
)

# --------------------------------------------------
# FUNZIONE DOJI MIGLIORATA
# --------------------------------------------------
def classify_doji(row):
    o, c, h, l = row["Open"], row["Close"], row["High"], row["Low"]

    body = abs(c - o)
    rng = h - l

    if rng == 0:
        return None

    upper = h - max(o, c)
    lower = min(o, c) - l

    body_pct = body / rng

    # Non è una doji
    if body_pct > max_body_pct:
        return None

    # Dragonfly Doji
    if lower > upper * dominance_ratio and body <= lower * body_shadow_ratio:
        return "Dragonfly Doji"

    # Gravestone Doji
    if upper > lower * dominance_ratio and body <= upper * body_shadow_ratio:
        return "Gravestone Doji"

    # Doji classica
    return "Doji"

# --------------------------------------------------
# LETTURA TICKER
# --------------------------------------------------
if not uploaded_file:
    st.warning("⬅️ Carica un file .txt con i ticker (uno per riga)")
    st.stop()

tickers = uploaded_file.read().decode("utf-8").splitlines()
tickers = [t.strip().upper() for t in tickers if t.strip()]

# --------------------------------------------------
# SCREENING
# --------------------------------------------------
results = []

with st.spinner("🔍 Screening in corso..."):
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)

            # Prezzi
            df = stock.history(period="7d")
            if len(df) < 2:
                continue

            yesterday = df.iloc[-2]
            doji_type = classify_doji(yesterday)

            if not doji_type:
                continue

            # Earnings
            cal = stock.calendar
            if cal.empty:
                continue

            earnings_date = cal.loc["Earnings Date"][0].date()
            if earnings_date != date.today():
                continue

            # TradingView link
            tv_symbol = ticker.replace(".MI", "")
            tv_link = f"https://www.tradingview.com/chart/?symbol=BIST:{tv_symbol}"

            results.append({
                "Ticker": ticker,
                "Doji Type": doji_type,
                "Earnings": earnings_date,
                "TradingView": tv_link
            })

        except Exception:
            continue

# --------------------------------------------------
# OUTPUT
# --------------------------------------------------
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
    st.info("Nessun titolo trovato con i criteri attuali.")

# --------------------------------------------------
# FOOTER DEBUG (opzionale)
# --------------------------------------------------
with st.expander("🧪 Debug (facoltativo)"):
    st.write(
        "La classificazione usa **rapporti relativi**, non soglie rigide. "
        "Questo replica il giudizio visivo del trader."
    )
