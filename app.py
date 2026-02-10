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

    # 🟢 Dragonfly / pseudo-dragonfly
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

            # ultima candela CHIUSA
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

            earnings_date = cal.loc["Earnings Date"].iat[0].date()
            if earnings_date != date.today():
                continue

            # --- TradingView link corretto per Milano ---
            tv_symbol = ticker.replace(".MI", "")
            tv_link = f"https://www.tradingview.com/chart/?symbol=MIL:{tv_symbol}"

            # --- Salvataggio risultati ---
            results.append({
                "Ticker": ticker,
                "Doji Type": doji_type,
                "Candle Date": candle.name.date(),
                "Earnings": earnings_date,
                "TradingView": tv_link
            })

            if show_debug:
                debug_rows.append({
                    "Ticker": ticker,
                    "Body %": round(body_pct, 2),
                    "Lower Shadow %": round(lower_pct, 2),
                    "Upper Shadow %": round(upper_pct, 2),
                    "Date": candle.name.date()
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
# DEBUG VISIVO
# --------------------------------------------------
if show_debug and debug_rows:
    st.subheader("🧪 Debug Doji (numeri reali)")
    st.dataframe(pd.DataFrame(debug_rows), use_container_width=True)
