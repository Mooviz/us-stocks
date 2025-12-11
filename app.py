import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Mooviz - Free US Stock Screener")

st.title("🌟 Mooviz: 완전 무료 미국 주식 Finviz 클론 🇺🇸")
st.markdown("아래 5개 검색창에 티커 입력 (e.g., AAPL, NVDA, TSLA) → 자동으로 데이터 불러와서 비교! 빈 칸 OK ♡")

# 검색창 5개
col1, col2, col3, col4, col5 = st.columns(5)
t1 = col1.text_input("티커 1", "AAPL").upper().strip()
t2 = col2.text_input("티커 2", "NVDA").upper().strip()
t3 = col3.text_input("티커 3", "TSLA").upper().strip()
t4 = col4.text_input("티커 4", "").upper().strip()
t5 = col5.text_input("티커 5", "").upper().strip()

tickers = [t for t in [t1, t2, t3, t4, t5] if t]

if not tickers:
    st.warning("티커 하나 이상 입력해주세요!")
    st.stop()

st.info(f"입력 티커: {', '.join(tickers)} – 로딩 중...")

@st.cache_data(ttl=300)
def get_data(tickers):
    data = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            hist = tk.history(period="1y")["Close"].dropna()
            
            # RSI 계산 (표준 공식, 안전하게)
            if len(hist) >= 14:
                delta = hist.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / loss
                rs = rs.replace([float('inf')], 100)  # inf 방지
                rs = rs.fillna(0)
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
            else:
                rsi = 50.0
            
            data.append({
                'Ticker': t,
                'Price': round(info.get('regularMarketPrice', info.get('previousClose', 0)), 2),
                'Change %': round(info.get('regularMarketChangePercent', 0), 2),
                'PER': round(info.get('forwardPE', info.get('trailingPE', 0)), 2) if info.get('forwardPE') or info.get('trailingPE') else 'N/A',
                'Volume (M)': round(info.get('volume', 0) / 1_000_000, 1),
                'Market Cap (B)': round(info.get('marketCap', 0) / 1_000_000_000, 1),
                'RSI': round(rsi, 2)
            })
        except Exception:
            data.append({
                'Ticker': t,
                'Price': 'Error',
                'Change %': 0,
                'PER': 'N/A',
                'Volume (M)': 0,
                'Market Cap (B)': 0,
                'RSI': 50
            })
    return pd.DataFrame(data)

df = get_data(tickers)

# 슬라이더 (기본값 완화해서 데이터 잘 나옴)
c1, c2, c3 = st.columns(3)
per_max = c1.slider("PER 최대", 0, 1000, 100)
vol_min = c2.slider("거래량 최소 (백만)", 0, 5000, 0)
rsi_max = c3.slider("RSI 최대 (과매도 30 추천)", 0, 150, 100)

# 필터 (PER N/A 제외)
df_num = df[df['PER'] != 'N/A'].copy()
df_num['PER'] = pd.to_numeric(df_num['PER'])
filtered = df_num[
    (df_num['PER'] <= per_max) &
    (df_num['Volume (M)'] >= vol_min) &
    (df_num['RSI'] <= rsi_max)
].sort_values('Change %', ascending=False)

st.subheader(f"입력 {len(tickers)}개 → 필터 통과 {len(filtered)}개")
st.dataframe(filtered)  # 기본 테이블 (색상 없이 안전하게)

# 히트맵
if not filtered.empty:
    fig = px.treemap(filtered, path=['Ticker'], values='Market Cap (B)',
                     color='Change %', color_continuous_scale='RdYlGn',
                     hover_data=['Price', 'PER', 'RSI', 'Volume (M)'])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("필터에 맞는 주식 없어요 – 슬라이더 넓혀보세요!")

st.subheader("전체 데이터 (필터 전)")
st.dataframe(df)

st.success(RSI 슬라이더 150으로 하면 다 보여요 ♡")
st.balloons()


