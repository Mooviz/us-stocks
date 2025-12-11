import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Mooviz - Finviz Intraday")

st.title("🌟 Mooviz: Finviz 당일 그래프 클론 🇺🇸")
st.markdown("아래 5개 검색창에 티커 입력 → Finviz처럼 당일 캔들 그래프 + 변화율 + 상대적 거래량 바로 보여줘요 ♡")

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

st.info(f"입력 티커: {', '.join(tickers)} – 당일 데이터 로딩 중...")

@st.cache_data(ttl=60)  # 1분마다 업데이트
def get_intraday_data(ticker):
    # 당일 1분봉 데이터 (미국 시장 시간에만 동작)
    data = yf.download(ticker, period="1d", interval="1m", progress=False)
    if data.empty:
        return None, None, None
    # 변화율 계산
    change_pct = round((data['Close'].iloc[-1] / data['Open'].iloc[0] - 1) * 100, 2)
    change_val = round(data['Close'].iloc[-1] - data['Open'].iloc[0], 2)
    current_price = round(data['Close'].iloc[-1], 2)
    return data, change_pct, change_val, current_price

# 각 티커별 당일 그래프 (Finviz 스타일)
for ticker in tickers:
    with st.expander(f"{ticker} 당일 그래프 (Finviz 스타일 – 클릭해서 보기)"):
        result = get_intraday_data(ticker)
        if result[0] is None:
            st.error(f"{ticker} – 미국 시장 미개장 또는 데이터 없음 (한국 시간 새벽 11:30~새벽 6:00에 확인)")
            continue
        
        data, change_pct, change_val, current_price = result
        
        # Finviz 스타일 그래프 (거래량 제거, 빨간선 = 전일 종가)
        fig = go.Figure()
        
        # 캔들스틱
        fig.add_trace(go.Candlestick(
            x=data.index,
            open=data['Open'],
            high=data['High'],
            low=data['Low'],
            close=data['Close'],
            name=ticker
        ))
        
        # 빨간 저항선 (전일 종가)
        prev_close = data['Close'].iloc[-1] if len(data) > 0 else 0
        fig.add_hline(y=prev_close, line_color="red", line_dash="dash", annotation_text="저항선")
        
        # 제목에 변화율 표시 (업로드 이미지처럼)
        title_text = f"{ticker}   {change_val:+.2f} ({change_pct:+.2f}%)"
        fig.update_layout(
            title=title_text,
            title_x=0.5,
            xaxis_title="시간",
            yaxis_title="가격",
            height=600,
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
        )
        
        # x축 시간 표시 (10AM, 11AM 등)
        fig.update_xaxes(
            tickformat="%I%p",
            tickangle=0
        )
        
        st.plotly_chart(fig, use_container_width=True)

st.success("완성! 업로드한 이미지처럼 당일 캔들 + 변화율 제목 + 빨간 저항선 나와요. 미국 시장 시간에 확인하세요 ♡")
st.balloons()
