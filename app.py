import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Mooviz - Free US Stock Screener")

st.title("🌟 Mooviz: 완전 무료 미국 주식 Finviz 클론 🇺🇸 (캔들 차트 완벽 고침!)")
st.markdown("아래 5개 검색창에 티커 입력 → 테이블 + 히트맵 + 각 주식별 Finviz 스타일 캔들 차트 ♡")

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
def get_summary_data(tickers):
    data = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            info = tk.info
            hist = tk.history(period="1y")["Close"].dropna()
            
            if len(hist) >= 14:
                delta = hist.diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = -delta.where(delta < 0, 0).rolling(14).mean()
                rs = gain / loss
                rs = rs.replace([float('inf')], 100).fillna(0)
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
        except:
            data.append({'Ticker': t, 'Price': 'Error', 'Change %': 0, 'PER': 'N/A', 'Volume (M)': 0, 'Market Cap (B)': 0, 'RSI': 50})
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def get_full_data(ticker):
    return yf.download(ticker, period="1y", progress=False)

summary_df = get_summary_data(tickers)

# 슬라이더
c1, c2, c3 = st.columns(3)
per_max = c1.slider("PER 최대", 0, 200, 100)
vol_min = c2.slider("거래량 최소 (백만)", 0, 500, 0)
rsi_max = c3.slider("RSI 최대", 0, 100, 100)

df_num = summary_df[summary_df['PER'] != 'N/A'].copy()
df_num['PER'] = pd.to_numeric(df_num['PER'])
filtered = df_num[
    (df_num['PER'] <= per_max) &
    (df_num['Volume (M)'] >= vol_min) &
    (df_num['RSI'] <= rsi_max)
].sort_values('Change %', ascending=False)

st.subheader(f"입력 {len(tickers)}개 → 필터 통과 {len(filtered)}개")
st.dataframe(filtered)

if not filtered.empty:
    fig_tree = px.treemap(filtered, path=['Ticker'], values='Market Cap (B)', color='Change %', color_continuous_scale='RdYlGn', hover_data=['Price', 'PER', 'RSI'])
    st.plotly_chart(fig_tree, use_container_width=True)

# 캔들 차트 섹션 (expander 안에서 버그 피하기 위해 height 고정 + use_container_width)
st.subheader("📈 각 주식 캔들스틱 차트 (Finviz 스타일 – 클릭해서 확대!)")
for ticker in tickers:
    with st.expander(f"{ticker} 캔들 차트 (최근 1년 + 거래량 – 클릭해서 열기)"):
        full_data = get_full_data(ticker)
        if not full_data.empty:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, subplot_titles=(f'{ticker} 가격', '거래량'), row_heights=[0.7, 0.3])
            fig.add_trace(go.Candlestick(x=full_data.index,
                                         open=full_data['Open'],
                                         high=full_data['High'],
                                         low=full_data['Low'],
                                         close=full_data['Close'],
                                         name="캔들"), row=1, col=1)
            fig.add_trace(go.Bar(x=full_data.index, y=full_data['Volume'], name="거래량", marker_color='lightblue'), row=2, col=1)
            fig.update_layout(height=700, xaxis_rangeslider_visible=False, title_text=f"{ticker} Finviz 스타일 차트")
            fig.update_yaxes(title_text="가격", row=1, col=1)
            fig.update_yaxes(title_text="거래량", row=2, col=1)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"{ticker} 차트 데이터 로드 실패 – 나중에 다시 시도!")

st.success("그래프 완벽 고침! expander 열고 마우스로 확대/이동 해보세요. Finviz 그대로예요 ♡")
st.balloons()
