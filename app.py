import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date, timedelta

st.set_page_config(page_title="Scanner Doji & Earnings", layout="wide")

st.title("🎯 Scanner Avanzato: Doji + Earnings Domani")
st.write(f"Oggi: **{date.today()}** | Analisi per: **{date.today() + timedelta(days=1)}**")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Parametri")
    threshold = st.slider("Tolleranza Doji (Corpo/Range)", 0.01, 0.50, 0.25, 0.01)
    st.info("Nota: Se non trovi nulla, aumenta la tolleranza (es. 0.30).")

def get_analysis(ticker_symbol, threshold):
    try:
        t_obj = yf.Ticker(ticker_symbol)
        df = t_obj.history(period="1mo", interval="1d")
        
        if df.empty or len(df) < 2:
            return None
            
        today_row = df.iloc[-1]
        o, h, l, c = float(today_row['Open']), float(today_row['High']), float(today_row['Low']), float(today_row['Close'])
        
        body = abs(c - o)
        total_range = h - l
        ratio = body / total_range if total_range != 0 else 0
        
        # Filtro Doji
        if ratio <= threshold:
            tomorrow = date.today() + timedelta(days=1)
            earnings_date_str = "N/A"
            is_tomorrow = False
            
            # Recupero Calendario
            try:
                cal = t_obj.calendar
                # Verifichiamo se cal è un dizionario e ha la chiave corretta
                if isinstance(cal, dict) and 'Earnings Date' in cal:
                    e_dates = cal['Earnings Date']
                    if e_dates:
                        # Prendiamo la prima data
                        d = e_dates[0]
                        # Convertiamo in oggetto date puro
                        d_pure = d.date() if hasattr(d, 'date') else d
                        earnings_date_str = d_pure.strftime('%Y-%m-%d')
                        
                        if d_pure == tomorrow:
                            is_tomorrow = True
            except: 
                pass

            return {
                "Ticker": ticker_symbol,
                "Prezzo": round(c, 2),
                "Ratio %": f"{round(ratio * 100, 1)}%",
                "Data Utili": earnings_date_str,
                "Earnings Domani": "🔥 SÌ" if is_tomorrow else "No",
                "df": df,
                "raw_ratio": ratio
            }
        return None
    except:
        return None

# --- Input Tickers ---
default_tickers = "A,AA,AAL,AAOI,AAPL,ABBV,ABNB,ABT,ACAD,ACHR,ACLS,ACN,ACNB,ADBE,ADI,ADP,ADSK,AEM,AEP,AESI,AFL,AFRM,AI,AIG,AKRO,ALB,ALC,ALK,ALL,ALLY,ALV,AMAT,AMD,AMGN,AMZN,ANET,ANF,APA,APD,APP,APLS,APTV,AR,ARLP,ARM,ARMK,ARVN,ASAN,ASML,ATEC,ATEX,AUPH,AVGO,AVTR,AXP,AZN,BA,BABA,BAC,BAX,BBIO,BBW,BBY,BE,BEAM,BEKE,BEN,BHP,BIDU,BIIB,BILI,BILL,BK,BKE,BKR,BKNG,BLK,BMY,BP,BRBR,BRK.A,BRK.B,BSM,BSX,BTU,BWA,BX,BXC,BYND,BWXT,C,CB,CBFV,CBT,CCJ,CCL,CDNS,CDW,CEG,CELH,CALM,CARR,CAT,CATY,CAVA,CFG,CFLT,CG,CHH,CHKP,CHTR,CL,CLF,CLS,CLSK,CMCSA,CME,CMG,CNH,CNM,CNQ,COF,COIN,COO,COP,COR,COST,CPB,CPK,CPNG,CPRT,CRBG,CRCL,CRDO,CRM,CROX,CRSP,CRWD,CSCO,CSGP,CSGS,CSX,CSTM,CTSH,CTVA,CTXR,CVEO,CVNA,CVS,CVX,CWAN,CZR,DAL,DASH,DB,DBX,DD,DDOG,DE,DELL,DEO,DG,DHI,DHR,DIS,DJT,DKNG,DKS,DLTR,DMLP,DOCU,DPZ,DT,DTE,DUK,DUOL,DVN,DXC,DXCM,EA,EB,EBAY,EBF,ECL,EDU,EGO,EH,EHAB,EL,ELV,EME,EMR,ENPH,ENR,ENVX,EOG,EQT,ET,ETN,ETSY,EVH,EWBC,EXAS,EXC,EXP,EXPE,EXTR,F,FANG,FAST,FDX,FE,FIS,FITBP,FL,FLEX,FNB,FOUR,FOXA,FRO,FROG,FSLR,FSLY,FTDR,FTI,FTNT,FTV,FUTU,FWONK,GAP,GE,GEHC,GEV,GES,GFS,GILD,GIS,GLW,GM,GNRC,GOOG,GOOGL,GTLB,GRMN,GRPN,GS,GT,GTX,GWAV,HAL,HASI,HBANM,HD,HIMS,HOG,HON,HOOD,HPE,HPQ,HSY,HUN,HVT,HWM,HTBK,IBEX,IBM,IBP,ICE,IIIN,ILMN,IMAX,IMCC,IMVT,INMD,INFY,ING,INSW,INTC,INTU,IOT,IPG,IRDM,ISRG,ITW,JCI,JD,JEF,JJSF,JNJ,JPM,JWEL,KAR,KARO,KDP,KHC,KLG,KLAC,KMI,KKR,KO,KR,KTOS,LAMR,LEN,LEVI,LGIH,LI,LIN,LLY,LMT,LNTH,LOW,LRCX,LSCC,LULU,LUV,LVS,LYFT,LYV,MA,MANU,MAR,MAT,MBLY,MC,MCD,MCHP,MCK,MCO,MDB,MDLZ,MDT,MED,META,MET,METC,MGM,MKC,MMM,MNDY,MNST,MO,MORN,MOS,MOV,MPC,MPLX,MRK,MRNA,MRVL,MS,MSFT,MSTR,MTCH,MTG,MU,MYGN,NCLH,NEE,NEM,NET,NFE,NFLX,NKE,NKSH,NOC,NOW,NTRA,NTRS,NTAP,NTLA,NTNX,NUE,NVR,NVDA,NVO,NVS,NVST,NWS,NXPI,OC,ODFL,OFLX,OKTA,OLN,ON,ONON,OPCH,ORCL,OTIS,OXY,OXM,PACB,PANW,PARA,PATH,PAYO,PAYX,PBFS,PBF,PBA,PCAR,PCG,PCRX,PD,PEP,PDD,PENN,PFE,PFS,PG,PGR,PHM,PINS,PLTR,PLUG,PM,POLA,POOL,PPG,PR,PRU,PSFE,PSMT,PSTG,PSX,PTC,PTEN,PVH,PYPL,QCOM,QGEN,RAIL,RACE,RBLX,RCL,RDN,RELY,RGEN,RGLD,RGR,RILY,RL,RMD,ROKU,ROL,ROOT,ROP,ROST,RF,RY,RXRX,S,SAM,SBUX,SCHL,SCHW,SDGR,SE,SEDG,SHAK,SHEL,SHOP,SHW,SIRI,SKX,SLB,SLGN,SM,SMCI,SNAP,SNEX,SNOW,SNPS,SNY,SO,SOFI,SONO,SOUN,SPGI,SPR,SRPT,SSTK,STLA,STT,STVN,STZ,SU,SYBT,SYK,SYPR,SYM,T,TBBK,TCX,TDOC,TDW,TECH,TECK,TER,TEM,TFC,TGT,TGTX,TJX,TM,TMDX,TMO,TMUS,TOST,TPB,TPR,TRGP,TRI,TRIP,TROW,TRV,TSLA,TSM,TSN,TTD,TTGT,TTWO,TWLO,TWST,TXG,TXN,U,UAL,UHAL,UBCP,UBER,UBS,UGI,UI,UNFI,UNH,UNP,UPS,UPST,UPWK,USB,VALE,V,VCYT,VEEV,VECO,VIPS,VKTX,VLO,VNOM,VOD,VREX,VRSK,VRSN,VRT,VRTX,VSAT,VSCO,VTRS,VZ,W,WAL,WBA,WBD,WDAY,WDC,WDFC,WFC,WHR,WIX,WM,WMG,WMT,WGS,WVE,WYNN,XEL,XENE,XOM,XPEV,XPER,XPO,XP,XYZ,YELP,YORW,YUM,Z,ZIM,ZION,ZM,ZS,ZTO,ZTS"

uploaded_file = st.file_uploader("Carica lista ticker (.txt)", type="txt")

if st.button("Avvia Scansione"):
    if uploaded_file:
        content = uploaded_file.getvalue().decode("utf-8")
    else:
        content = default_tickers
    
    clean_content = content.replace(',', ' ').replace('\n', ' ').replace('\r', ' ')
    tickers = [t.strip().upper() for t in clean_content.split(' ') if t.strip()]
    
    results = []
    progress_bar = st.progress(0)
    for i, t in enumerate(tickers):
        res = get_analysis(t, threshold)
        if res:
            results.append(res)
        progress_bar.progress((i + 1) / len(tickers))
    
    st.session_state['results'] = results

# --- Visualizzazione ---
if 'results' in st.session_state:
    res_list = st.session_state['results']
    
    if len(res_list) > 0:
        # Qui evitiamo il KeyError controllando se la lista non è vuota
        df_display = pd.DataFrame(res_list)
        
        # Pulizia colonne per la tabella
        cols_to_keep = ["Ticker", "Prezzo", "Ratio %", "Data Utili", "Earnings Domani"]
        st.subheader(f"Trovate {len(res_list)} Doji")
        
        # Mostriamo la tabella
        st.dataframe(df_display[cols_to_keep].sort_values(by="Earnings Domani", ascending=False), use_container_width=True)
        
        st.divider()
        ticker_to_show = st.selectbox("Seleziona ticker per il grafico:", [r['Ticker'] for r in res_list])
        selected_data = next(item for item in res_list if item["Ticker"] == ticker_to_show)
        
        fig = go.Figure(data=[go.Candlestick(
            x=selected_data['df'].index,
            open=selected_data['df']['Open'], high=selected_data['df']['High'],
            low=selected_data['df']['Low'], close=selected_data['df']['Close']
        )])
        fig.update_layout(template="plotly_dark", title=f"{ticker_to_show} - Prossimi Utili: {selected_data['Data Utili']}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nessuna Doji trovata. Prova ad alzare la 'Tolleranza Doji' nella barra laterale.")