import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Mooviz")

st.title("🌟 Mooviz – 당신만의 미국 주식 Finviz")
st.markdown("아래 5개 검색창에 원하는 티커를 입력하세요 (예: AAPL NVDA TSLA) → 자동으로 비교해줍니다!")

# ← 여기부터가 검색창 5개
col1, col2, col3, col4, col5 = st.columns(5)
t1 = col1.text_input("티커 1", "AAPL").upper().strip()
t2 = col2.text_input("티커 2", "NVDA").upper().strip()
t3 = col3.text_input("티커 3", "TSLA").upper().strip()
t4 = col4.text_input("티커 4", "").upper().strip()
t5 = col5.text_input("티커 5", "").upper().strip()

tickers = [t for t in [t1, t2, t3, t4, t5] if t]  # 빈칸 제거

if not tickers:
    st.stop()

@st.cache_data(ttl=180)
def get_data(tickers):
    data = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            hist = tk.history(period="1y")["Close"]
            rsi = 50 if len(hist)<20 else round((hist.pct_change().dropna() > 0).rolling(14).mean().iloc[-1] * 100, 1)
            data.append({
                "Ticker": t,
                "가격": info.get("regularMarketPrice", info.get("previousClose", 0)),
                "변화율": info.get("regularMarketChangePercent", 0),
                "PER": info.get("forwardPE") or info.get("trailingPE", "-"),
                "거래량(M)": round(info.get("volume",0)/1_000_000, 1),
                "시총(B)": round(info.get("marketCap",0)/1_000_000_000, 1),
                "RSI": rsi
            })
        except:
            data.append({"Ticker": t, "가격": "에러", "변화율": 0, "PER": "-", "거래량(M)": 0, "시총(B)": 0, "RSI": "-"})
    return pd.DataFrame(data)

df = get_data(tickers)

# 필터 슬라이더
c1, c2, c3 = st.columns(3)
per = c1.slider("PER 최대", 0, 100, 30)
vol = c2.slider("거래량 최소 (백만)", 0, 500, 5)
rsi = c3.slider("RSI 최대", 0, 100, 70)

filtered = df[(df["PER"] != "-") & (df["PER"] <= per) & (df["거래량(M)"] >= vol) & (df["RSI"] <= rsi)]

st.subheader(f"입력 티커 {len(tickers)}개 → 필터 통과 {len(filtered)}개")
st.dataframe(filtered.style.background_gradient(cmap="RdYlGn", subset=["변화율"]))

# 히트맵
fig = px.treemap(filtered, path=["Ticker"], values="시총(B)", color="변화율",
                 color_continuous_scale="RdYlGn", hover_data=["가격","PER","RSI"])
st.plotly_chart(fig, use_container_width=True)

st.success("완성! 검색창에 원하는 티커 넣고 엔터 치기만 하면 돼요 ♡")
st.balloons()
