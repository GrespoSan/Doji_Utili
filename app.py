import streamlit as st
import yfinance as yf
import pandas as pd

# --------------------------------------------------
# CONFIG STREAMLIT
# --------------------------------------------------
st.set_page_config(
    page_title="Doji + Earnings Screener Italia",
    layout="wide"
)

st.title("📊 Screener Pseudo-Doji – Italia")
st.write(
    "Mostra tutte le pseudo-doji dell'ultima candela disponibile per titoli italiani "
    "anche se Yahoo non riporta earnings."
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

    # Super-permissiva: corpo piccolo ≤50% del range
    if body_pct <= 0.5:
        return "Pseudo-Doji", (body_pct, upper_pct, lower_pct)
    return None, None

# --------------------------------------------------
# SCREENING
# --------------------------------------------------
results = []

with st.spinner("🔍 Screening pseudo-doji in corso..."):
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period="10d", interval="1d")
            if df.empty:
                continue

            # Prendi l'ultima candela disponibile
            candle = df.iloc[-1]

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

            # DEBUG: ultimi 5 giorni per controllo visivo
            if show_debug:
                st.subheader(f"Ultimi 5 giorni: {ticker}")
                st.dataframe(df.tail(5))

        except Exception:
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

else:
    st.info("Nessuna pseudo-doji trovata nei ticker caricati.")
