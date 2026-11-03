import pandas as pd
import numpy as np

def calc_all_indicator(df):
    # MA均线
    for n in [5, 10, 20, 60]:
        df[f"MA{n}"] = df["close"].rolling(n).mean()

    # MACD
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["DIF"] = ema12 - ema26
    df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
    df["MACD"] = (df["DIF"] - df["DEA"]) * 2

    # RSI
    diff = df["close"].diff()
    up = diff.where(diff > 0, 0.0)
    dn = -diff.where(diff < 0, 0.0)
    avg_up = up.rolling(14).mean()
    avg_dn = dn.rolling(14).mean()

    # 先把 avg_dn 中的 0 换成 NaN，避免除零警告
    rs = avg_up / avg_dn.replace(0, np.nan)
    rsi = 100 - 100 / (1 + rs)

    # 边界修正：14 天纯上涨 -> 100；14 天横盘(涨跌幅全为 0) -> 50
    rsi = rsi.mask((avg_dn == 0) & (avg_up > 0), 100.0)
    rsi = rsi.mask((avg_dn == 0) & (avg_up == 0), 50.0)
    df["RSI"] = rsi

    return df
