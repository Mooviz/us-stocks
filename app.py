import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Mooviz - Free US Stock Screener")

st.title("🌟 Mooviz: 완전 무료 미국 주식 Finviz 클론 🇺🇸")
st.markdown("아래 5개 검색창에 티커 입력 (e.g., AAPL, NVDA, TSLA) → 자동 비교! 빈 칸은 무시 ♡")

# 검색창: 5개 컬럼으로 입력
col1, col2, col3, col4, col5 = st.columns(5)
t1 = col1.text_input("티커 1", "AAPL").upper().strip()
t2 = col2.text_input("티커 2", "NVDA").upper().strip()
t3 = col3.text_input("티커 3", "TSLA").upper().strip()
t4 = col4.text_input("티커 4", "").upper().strip()
t5 = col5.text_input("티커 5", "").upper().strip()

tickers = [t for t in [t1, t2, t3, t4, t5] if t]  # 빈칸 제거

if not tickers:
    st.warning("하나 이상의 티커를 입력해주세요!")
    st.stop()

st.info(f"입력된 티커: {', '.join(tickers)} – 데이터 로딩 중...")

@st.cache_data(ttl=180)  # 3분 캐시
def get_data(tickers):
    data = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            hist = tk.history(period="1y")["Close"].dropna()
            
            # RSI 제대로 계산 (오타 수정: pct_change() 후 gain/loss)
            if len(hist) >= 14:
                delta = hist.diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
                rs = gain / loss
                rs = rs.fillna(0).replace([float('inf')], 0)
                rsi = 100 - (100 / (1 + rs)).iloc[-1]
            else:
                rsi = 50
            
            data.append({
                'Ticker': t,
                'Price': round(info.get('regularMarketPrice', info.get('previousClose', 0)), 2),
                'Change %': round(info.get('regularMarketChangePercent', 0), 2),
                'PER': round(info.get('forwardPE', info.get('trailingPE', 0)), 2) if info.get('forwardPE') or info.get('trailingPE') else 'N/A',
                'Volume (M)': round(info.get('volume', 0) / 1_000_000, 1),
                'Market Cap (B)': round(info.get('marketCap', 0) / 1_000_000_000, 1),
                'RSI': round(rsi, 2)
            })
        except Exception as e:
            st.error(f"{t} 에러: {str(e)} – 티커 확인!")
            data.append({'Ticker': t, 'Price': 0, 'Change %': 0, 'PER': 'N/A', 'Volume (M)': 0, 'Market Cap (B)': 0, 'RSI': 50})
    return pd.DataFrame(data)

df = get_data(tickers)

# 필터 슬라이더 (기본값 완화: PER 50, Volume 1, RSI 80으로 해서 데이터 잘 나옴)
col_f1, col_f2, col_f3 = st.columns(3)
per_max = col_f1.slider("PER 최대 (N/A 무시)", 0, 100, 50)  # 50으로 완화
vol_min = col_f2.slider("거래량 최소 (백만)", 0, 500, 1)  # 1로 완화
rsi_max = col_f3.slider("RSI 최대 (과매도 30 추천)", 0, 100, 80)  # 80로 완화

# PER가 숫자만 필터 (N/A 제외)
df_numeric = df[df['PER'] != 'N/A'].copy()
df_numeric['PER'] = pd.to_numeric(df_numeric['PER'])

filtered = df_numeric[
    (df_numeric['PER'] <= per_max) &
    (df_numeric['Volume (M)'] >= vol_min) &
    (df_numeric['RSI'] <= rsi_max)
].sort_values('Change %', ascending=False)

st.subheader(f"📊 입력 {len(tickers)}개 → 필터 통과 {len(filtered)}개 (전체 테이블 아래)")

# 테이블 (background_gradient로 색상, 영어 라벨로 포맷 안정화)
st.dataframe(filtered.style.background_gradient(cmap='RdYlGn', subset=['Change %'], low=0, high=0.2))

# 히트맵 (Plotly로 변화율 색상)
st.subheader("🌈 히트맵: 변화율 한눈에 (클릭/호버 해보세요!)")
fig = px.treemap(filtered, path=['Ticker'], values='Market Cap (B)',
                 color='Change %', color_continuous_scale='RdYlGn',
                 hover_data=['Price', 'PER', 'RSI', 'Volume (M)'],
                 title="Market Cap 기준 히트맵")
st.plotly_chart(fig, use_container_width=True)

# 전체 테이블 (필터 안 거친 원본 데이터 확인용)
st.subheader("📋 전체 원본 데이터 (필터 전)")
st.dataframe(df.style.background_gradient(cmap='RdYlGn', subset=['Change %']))

st.success("고침! 이제 PER 50, 거래량 1M, RSI 80 기본으로 데이터 잘 나와요. 슬라이더 조정해보세요 ♡")
st.balloons()
