import streamlit as st
import pandas as pd
from data_fetcher import get_stock_data, get_hs300_data, get_stock_pe
from indicator import calc_all_indicator
from strategy import backtest_strategy
from chart_draw import draw_main_chart, draw_return_chart

st.set_page_config(page_title="高级股票可视化分析系统", layout="wide")
st.markdown("<h1 style='text-align:center;color:#42A5F5'>📈 Python高级股票可视化分析系统</h1>",unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("参数设置")
    code = st.text_input("股票代码","601318")
    start = st.date_input("起始日期",pd.to_datetime("2024-01-01"))
    end = st.date_input("结束日期",pd.to_datetime("2026-10-01"))
    run = st.button("开始分析")

if run:
    start_str = start.strftime("%Y%m%d")
    end_str = end.strftime("%Y%m%d")

    with st.spinner("正在获取数据、计算指标、执行策略回测..."):
        df = get_stock_data(code, start_str, end_str)
        if df.empty:
            st.error("数据获取失败！请检查代码或网络")
        else:
            df = calc_all_indicator(df)
            bench = get_hs300_data(start_str, end_str)
            res = backtest_strategy(df, bench)
            df_back = res["data"]

            # 基本面信息
            pe = get_stock_pe(code)
            if pe is not None:
                st.write(f"市盈率PE(TTM): {pe:.2f}")
            else:
                st.write("市盈率PE(TTM): 数据源暂不支持")

            # 回测指标展示
            st.subheader("📊 策略回测绩效指标")
            col1,col2,col3,col4 = st.columns(4)
            col1.metric("策略总收益(%)", res["策略总收益"])
            col2.metric("大盘基准收益(%)", res["基准收益"] if res["基准收益"] is not None else "N/A")
            col3.metric("最大回撤(%)", res["最大回撤"])
            col4.metric("交易次数", res["交易次数"])

            # K线总图
            st.subheader("📈 股票K线+全指标走势图")
            fig1 = draw_main_chart(df_back)
            st.plotly_chart(fig1, use_container_width=True)

            # 收益对比图
            st.subheader("📈 策略收益 VS 大盘收益曲线")
            fig2 = draw_return_chart(df_back)
            st.plotly_chart(fig2, use_container_width=True)

            # 数据导出
            csv = df_back.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 下载完整分析数据", csv, f"{code}_完整数据.csv")

st.markdown("---")
st.caption("本系统仅用于学习研究，不构成任何投资建议 | 数据源：公开财经数据")
