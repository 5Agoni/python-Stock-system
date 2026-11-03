import plotly.graph_objects as go
from plotly.subplots import make_subplots

def draw_main_chart(df):
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.4,0.15,0.2,0.25]
    )

    # K线
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="K线"
    ), row=1, col=1)

    # 均线
    for name in ["MA5","MA10","MA20","MA60"]:
        fig.add_trace(go.Scatter(x=df["date"], y=df[name], name=name), row=1, col=1)

    # 成交量
    fig.add_trace(go.Bar(x=df["date"], y=df["volume"], name="成交量"), row=2, col=1)

    # MACD
    fig.add_trace(go.Scatter(x=df["date"], y=df["DIF"], name="DIF"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df["date"], y=df["DEA"], name="DEA"), row=3, col=1)
    fig.add_trace(go.Bar(x=df["date"], y=df["MACD"], name="MACD柱"), row=3, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df["date"], y=df["RSI"], name="RSI"), row=4, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=4)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=4)

    fig.update_layout(height=900, template="plotly_dark", xaxis_rangeslider_visible=False)
    return fig

def draw_return_chart(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["cum_bench"], name="大盘基准收益", mode="lines"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["cum_strategy"], name="策略收益", mode="lines"))
    fig.update_layout(template="plotly_dark", title="策略VS大盘收益曲线")
    return fig
