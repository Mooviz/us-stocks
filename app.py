# Mooviz: 돈 없는 미국 주식쟁이를 위한 무료 Finviz 클론 🇺🇸
# 만든 사람: Grok ♡ (한국 팬 요청으로 Mooviz로 변경!)
# 2025년 12월 버전 - 더 많은 티커, 안정적 RSI, 히트맵 예쁘게

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(layout="wide", page_title="Mooviz - Free US Stock Screener")

st.title("🌟 Mooviz: 완전 무료 미국 주식 Finviz 클론 🇺🇸")
st.markdown("PER 낮은 주식, 거래량 많은 주식, RSI 과매도 주식 바로 찾아보세요! 티커 추가만 하면 무한 확장 가능 ♡")

# 더 많은 미국 인기 주식 티커 (S&P500 대표 + 테크/ETF)
tickers = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "BRK-B", "LLY", "JPM",
    "AMD", "NFLX", "ADBE", "CRM", "INTC", "PYPL", "DIS", "KO", "PFE", "XOM",
    "SOXL", "TQQQ", "SPY", "QQQ", "VOO"  # 추가 ETF/레버리지
]

@st.cache_data(ttl=300)  # 5분마다 업데이트
def get_data(tickers):
    df_list = []
    for tick in tickers:
        ticker = yf.Ticker(tick)
        info = ticker.info
        history = ticker.history(period="1y")['Close'].dropna()
        rsi = calculate_rsi(history) if len(history) > 14 else 50
        df_list.append({
            'Ticker': tick,
            'Price': info.get('regularMarketPrice', info.get('previousClose', 0)),
            'Change %': info.get('regularMarketChangePercent', 0),
            'PER': info.get('forwardPE', info.get('trailingPE', 0)),
            'Volume (M)': info.get('volume', 0) / 1_000_000,
            'Market Cap (B)': info.get('marketCap', 0) / 1_000_000_000,
            'RSI': round(rsi, 2)
        })
    return pd.DataFrame(df_list)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss.replace(0, float('inf'))
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else 50

# 데이터 불러오기
df = get_data(tickers)

# 스크리너
st.subheader("🔍 스크리너: 조건으로 필터링 (Finviz처럼!)")
col1, col2, col3 = st.columns(3)
with col1:
    per_max = st.slider("PER 최대", 0, 100, 25)
with col2:
    volume_min = st.slider("거래량 최소 (백만)", 0, 500, 10)
with col3:
    rsi_max = st.slider("RSI 최대 (과매도: 30 이하 추천)", 0, 100, 40)

filtered = df[
    (df['PER'] <= per_max) &
    (df['Volume (M)'] >= volume_min) &
    (df['RSI'] <= rsi_max)
].sort_values("Change %", ascending=False)

st.dataframe(filtered.style.background_gradient(cmap='RdYlGn', subset=['Change %']))

# 히트맵
st.subheader("🌈 히트맵: 변화율 색깔로 한눈에!")
fig = px.treemap(filtered, path=['Ticker'], values='Market Cap (B)',
                 color='Change %', color_continuous_scale='RdYlGn',
                 hover_data=['Price', 'PER', 'RSI'])
st.plotly_chart(fig, use_container_width=True)

st.success("Mooviz 완성! 티커 더 추가하려면 코드 상단 tickers 리스트에 '새티커' 넣으세요. (e.g., 'PLTR') ♡")
st.balloons()