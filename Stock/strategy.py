import pandas as pd
import numpy as np

def backtest_strategy(df, bench_df=None):
    d = df.copy().dropna().reset_index(drop=True)

    # 金叉死叉策略：MA5上穿MA20买入，下穿卖出
    d["golden"] = (d["MA5"] > d["MA20"]) & (d["MA5"].shift(1) <= d["MA20"].shift(1))
    d["dead"] = (d["MA5"] < d["MA20"]) & (d["MA5"].shift(1) >= d["MA20"].shift(1))

    # 持仓状态：金叉买入=1，死叉卖出=0（向量化，等价于逐行状态机）
    signal = d["golden"].astype(int) - d["dead"].astype(int)
    d["position"] = signal.cumsum().clip(0, 1)

    # 收益计算：信号滞后一天，避免“未来函数”
    d["return"] = d["close"].pct_change().fillna(0)
    d["strategy_return"] = d["return"] * d["position"].shift(1).fillna(0)
    d["cum_strategy"] = (1 + d["strategy_return"]).cumprod()

    # 基准收益（沪深300）
    if bench_df is not None and not bench_df.empty:
        bench = bench_df[["date", "close"]].copy()
        bench["bench_return"] = bench["close"].pct_change().fillna(0)
        d = d.merge(bench[["date", "bench_return"]], on="date", how="left")
        d["bench_return"] = d["bench_return"].fillna(0)
        d["cum_bench"] = (1 + d["bench_return"]).cumprod()
    else:
        d["bench_return"] = np.nan
        d["cum_bench"] = np.nan

    # 最大回撤
    def max_drawdown(series):
        roll_max = series.cummax()
        drawdown = (series - roll_max) / roll_max
        return drawdown.min()

    # 统计指标
    total_ret = d["cum_strategy"].iloc[-1] - 1
    mdd = max_drawdown(d["cum_strategy"])
    trade_times = int(d["golden"].sum() + d["dead"].sum())

    has_bench = bench_df is not None and not bench_df.empty
    bench_ret = (d["cum_bench"].iloc[-1] - 1) if has_bench else None

    return {
        "data": d,
        "策略总收益": round(total_ret * 100, 2),
        "基准收益": round(bench_ret * 100, 2) if bench_ret is not None else None,
        "最大回撤": round(mdd * 100, 2),
        "交易次数": trade_times,
    }
