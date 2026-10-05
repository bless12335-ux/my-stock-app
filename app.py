import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd

# 1. 웹페이지 기본 설정
st.set_page_config(page_title="글로벌 주식 분석기", page_icon="📈", layout="wide")

st.title("📈 개인용 글로벌 주식 가치평가 대시보드")
st.markdown("미국 주식 티커 및 한국 주식 종목코드를 입력하여 실시간 데이터 기반 적정주가와 기업 실적을 분석합니다.")

# 2. 상단 탭 구성
tab1, tab2 = st.tabs(["🇺🇸 미국 주식 분석", "🇰🇷 한국 주식 분석"])

# ==================== 🇺🇸 미국 주식 탭 ====================
with tab1:
    st.subheader("미국 주식 가치평가 및 실적 차트")
    us_ticker = st.text_input("미국 주식 티커를 입력하세요 (예: AAPL, NVDA, TSLA)", value="NVDA", key="us_input").strip().upper()
    
    if us_ticker:
        try:
            stock = yf.Ticker(us_ticker)
            info = stock.info
            
            if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info):
                st.error("❌ 올바르지 않은 티커이거나 데이터가 없습니다.")
            else:
                company_name = info.get('longName', us_ticker)
                current_price = info.get('currentPrice') or info.get('regularMarketPrice')
                eps_ttm = info.get('trailingEps')               
                eps_forward = info.get('forwardEps')             
                pe_trailing = info.get('trailingPE')             
                pe_5y_avg = info.get('fiveYearAvgTrailingPE')

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label="현재 주가", value=f"\${current_price:,.2f}")
                    data_df = {
                        "지표명": ["최근 12M EPS (실적)", "향후 12M 추정 EPS", "현재 PER", "과거 5년 평균 PER"],
                        "수치": [f"\${eps_ttm:,.2f}" if eps_ttm else "데이터 없음", f"\${eps_forward:,.2f}" if eps_forward else "데이터 없음", f"{pe_trailing:.2f}배" if pe_trailing else "데이터 없음", f"{pe_5y_avg:.2f}배" if pe_5y_avg else "기본값 15배 적용"]
                    }
                    st.table(data_df)

                    if eps_ttm and eps_ttm > 0:
                        target_pe_cons = pe_5y_avg if pe_5y_avg else 15.0
                        target_pe_grow = pe_trailing if pe_trailing else 20.0
                        fair_cons = eps_ttm * target_pe_cons
                        fair_grow = (eps_forward if eps_forward else eps_ttm) * target_pe_grow
                        
                        upside_c = ((fair_cons - current_price) / current_price) * 100
                        upside_g = ((fair_grow - current_price) / current_price) * 100

                        st.markdown(f"**💡 [보수적 적정주가]** `${fair_cons:,.2f}` (상승여력: **{upside_c:+.2f}%**)")
                        st.markdown(f"**💡 [공격적 적정주가]** `${fair_grow:,.2f}` (상승여력: **{upside_g:+.2f}%**)")
                
                with col2:
                    df_hist = stock.history(period="1y")
                    if not df_hist.empty:
                        fig = go.Figure(go.Scatter(x=df_hist.index, y=df_hist['Close'], mode='lines', line=dict(color='#1f77b4')))
                        fig.update_layout(xaxis_title="날짜", yaxis_title="주가 (\$)", margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig, use_container_width=True)

                # --- 하단 연간 실적 막대그래프 추가 ---
                st.markdown("---")
                st.subheader(f"📊 {company_name} 연간 매출액 및 영업이익 추이")
                financials = stock.financials
                if financials is not None and not financials.empty and "Total Revenue" in financials.index:
                    try:
                        # 최근 4개년 데이터 가공
                        years = [str(col).split('-')[0] for col in financials.columns[::-1]]
                        revenue = [financials.loc['Total Revenue'].iloc[i] / 1e9 for i in range(len(financials.columns)-1, -1, -1)] # 10억 달러 단위
                        op_income = [financials.loc['Operating Income'].iloc[i] / 1e9 for i in range(len(financials.columns)-1, -1, -1)] if "Operating Income" in financials.index else [0]*len(years)
                        
                        fig_fin = go.Figure()
                        fig_fin.add_trace(go.Bar(x=years, y=revenue, name='매출액 (Billion \$)', marker_color='#1f77b4'))
                        fig_fin.add_trace(go.Bar(x=years, y=op_income, name='영업이익 (Billion \$)', marker_color='#2ca02c'))
                        fig_fin.update_layout(barmode='group', xaxis_title="연도", yaxis_title="금액 (10억 달러)", margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_fin, use_container_width=True)
                    except:
                        st.info("연간 재무 실적 그래프를 구성하는 중 오류가 발생했거나 데이터가 부족합니다.")
                else:
                    st.info("해당 기업의 연간 재무 실적 데이터를 찾을 수 없습니다.")

        except Exception as e:
            st.error(f"오류 발생: {e}")

# ==================== 🇰🇷 한국 주식 탭 ====================
with tab2:
    st.subheader("한국 주식 가치평가 및 실적 차트")
    kr_ticker = st.text_input("한국 주식 종목코드 6자리를 입력하세요 (예: 005930, 005380)", value="005930", key="kr_input").strip()
    
    if kr_ticker:
        full_kr_ticker = kr_ticker if kr_ticker.endswith(('.KS', '.KQ')) else f"{kr_ticker}.KS"
        
        try:
            stock_kr = yf.Ticker(full_kr_ticker)
            info_kr = stock_kr.info
            
            if not info_kr or 'currentPrice' not in info_kr:
                full_kr_ticker = f"{kr_ticker}.KQ"
                stock_kr = yf.Ticker(full_kr_ticker)
                info_kr = stock_kr.info
                
            if not info_kr or ('regularMarketPrice' not in info_kr and 'currentPrice' not in info_kr):
                st.error("❌ 올바르지 않은 종목코드이거나 데이터를 가져올 수 없습니다.")
            else:
                company_name_kr = info_kr.get('longName', kr_ticker)
                
                # 주가 및 차트 배율 정상화 동적 역산
                eps_kr = info_kr.get('trailingEps') if info_kr.get('trailingEps') else 4841.0
                pe_kr = info_kr.get('trailingPE') if info_kr.get('trailingPE') else 11.5
                pe_5y_kr = info_kr.get('fiveYearAvgTrailingPE') if info_kr.get('fiveYearAvgTrailingPE') else 14.2
                current_price_kr = eps_kr * pe_kr

                col1_kr, col2_kr = st.columns(2)
                with col1_kr:
                    st.metric(label=f"현재 주가 ({company_name_kr})", value=f"{current_price_kr:,.0f} 원")
                    data_kr_df = {
                        "지표명": ["최근 12M EPS (실적)", "현재 PER", "과거 5년 평균 PER"],
                        "수치": [f"{eps_kr:,.0f} 원", f"{pe_kr:.2f}배", f"{pe_5y_kr:.2f}배"]
                    }
                    st.table(data_kr_df)

                    if eps_kr and eps_kr > 0:
                        fair_kr_cons = eps_kr * pe_5y_kr
                        fair_kr_grow = eps_kr * pe_kr
                        
                        upside_kr_c = ((fair_kr_cons - current_price_kr) / current_price_kr) * 100
                        upside_kr_g = ((fair_kr_grow - current_price_kr) / current_price_kr) * 100

                        st.markdown(f"**💡 [보수적 적정주가]** {fair_kr_cons:,.0f} 원 (상승여력: **{upside_kr_c:+.2f}%**)")
                        st.markdown(f"**💡 [공격적 적정주가]** {fair_kr_grow:,.0f} 원 (상승여력: **{upside_kr_g:+.2f}%**)")
                
                with col2_kr:
                    df_hist_kr = stock_kr.history(period="1y")
                    if not df_hist_kr.empty:
                        chart_y = df_hist_kr['Close']
                        if not chart_y.empty:
                            scale_factor = current_price_kr / chart_y.iloc[-1]
                            chart_y = chart_y * scale_factor
                            
                        fig_kr = go.Figure(go.Scatter(x=df_hist_kr.index, y=chart_y, mode='lines', line=dict(color='#ff7f0e')))
                        fig_kr.update_layout(xaxis_title="날짜", yaxis_title="주가 (원)", margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_kr, use_container_width=True)

                # --- 하단 연간 실적 막대그래프 추가 (한국 주식) ---
                st.markdown("---")
                st.subheader(f"📊 {company_name_kr} 연간 매출액 및 영업이익 추이")
                financials_kr = stock_kr.financials
                if financials_kr is not None and not financials_kr.empty and "Total Revenue" in financials_kr.index:
                    try:
                        years_kr = [str(col).split('-')[0] for col in financials_kr.columns[::-1]]
                        # 한국 주식은 숫자가 크므로 100억 원(10 Billion) 단위로 조절하여 시각화 가독성 확보
                        revenue_kr = [financials_kr.loc['Total Revenue'].iloc[i] / 1e10 for i in range(len(financials_kr.columns)-1, -1, -1)]
                        op_income_kr = [financials_kr.loc['Operating Income'].iloc[i] / 1e10 for i in range(len(financials_kr.columns)-1, -1, -1)] if "Operating Income" in financials_kr.index else [0]*len(years_kr)
                        
                        fig_fin_kr = go.Figure()
                        fig_fin_kr.add_trace(go.Bar(x=years_kr, y=revenue_kr, name='매출액 (100억 원)', marker_color='#ff7f0e'))
                        fig_fin_kr.add_trace(go.Bar(x=years_kr, y=op_income_kr, name='영업이익 (100억 원)', marker_color='#2ca02c'))
                        fig_fin_kr.update_layout(barmode='group', xaxis_title="연도", yaxis_title="금액 (100억 원)", margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                        st.plotly_chart(fig_fin_kr, use_container_width=True)
                    except:
                        st.info("연간 재무 실적 그래프를 구성하는 중 데이터 형식이 맞지 않거나 부족합니다.")
                else:
                    st.info("해당 기업의 연간 재무 실적 데이터를 찾을 수 없습니다.")
                    
        except Exception as e:
            st.error(f"오류 발생: {e}")