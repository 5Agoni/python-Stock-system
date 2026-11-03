import akshare as ak
import pandas as pd
import os
import time

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def _with_exchange_prefix(symbol: str) -> str:
    """给 6 位股票代码加上交易所前缀，供新浪/腾讯数据源使用"""
    if symbol.startswith(("sh", "sz", "bj")):
        return symbol
    if symbol.startswith(("6", "9")):
        return "sh" + symbol
    if symbol.startswith(("4", "8")):
        return "bj" + symbol
    return "sz" + symbol


def get_stock_data(symbol: str, start_date: str, end_date: str, adjust="qfq") -> pd.DataFrame:
    cache_file = f"{CACHE_DIR}/{symbol}_{start_date}_{end_date}_{adjust}.csv"
    if os.path.exists(cache_file):
        return pd.read_csv(cache_file, parse_dates=["date"])

    # 多数据源依次尝试：东方财富被限流时自动切换到新浪
    sources = [
        ("东方财富", lambda: ak.stock_zh_a_hist(
            symbol=symbol, period="daily",
            start_date=start_date, end_date=end_date, adjust=adjust)),
        ("新浪", lambda: ak.stock_zh_a_daily(
            symbol=_with_exchange_prefix(symbol),
            start_date=start_date, end_date=end_date, adjust=adjust)),
    ]

    for name, fetch in sources:
        try:
            raw = fetch()
            if raw is None or raw.empty:
                print(f"{name}数据源返回空数据，尝试下一个...")
                continue
            df = raw.rename(columns={
                "日期": "date", "开盘": "open", "最高": "high",
                "最低": "low", "收盘": "close", "成交量": "volume",
            })
            cols = ["date", "open", "high", "low", "close", "volume"]
            if not all(c in df.columns for c in cols):
                print(f"{name}数据源缺少必要列，尝试下一个...")
                continue
            df = df[cols].copy()
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            df.to_csv(cache_file, index=False)
            print(f"已通过{name}数据源获取 {symbol} 数据")
            time.sleep(0.6)
            return df
        except Exception as e:
            msg = str(e)
            if "断开" in msg or "限流" in msg:
                print(f"{name}数据源被限流，尝试下一个...")
            else:
                print(f"{name}数据源获取失败：{msg}")
            continue
    return pd.DataFrame()

# 沪深300基准
def get_hs300_data(start_date, end_date):
    cache_file = f"{CACHE_DIR}/hs300_{start_date}_{end_date}.csv"
    if os.path.exists(cache_file):
        return pd.read_csv(cache_file, parse_dates=["date"])
    try:
        df = ak.stock_zh_index_daily(symbol="sh000300")
        # 兼容中英文列名
        df = df.rename(columns={
            "日期": "date", "收盘": "close", "开盘": "open",
            "最高": "high", "最低": "low", "成交量": "volume"
        })
        df["date"] = pd.to_datetime(df["date"])
        # 起止日期统一转成 datetime，避免字符串与日期比较出错
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        df = df[(df["date"] >= start) & (df["date"] <= end)]
        df = df[["date", "close"]].copy()
        df = df.sort_values("date").reset_index(drop=True)
        df.to_csv(cache_file, index=False)
        return df
    except Exception as e:
        print("沪深300获取失败：", e)
        return pd.DataFrame()

def get_stock_pe(symbol):
    # 用乐咕乐股单只股票估值接口，避开东方财富全市场快照（易触发限流），并按天缓存
    import datetime
    today = datetime.date.today().strftime("%Y%m%d")
    cache_file = f"{CACHE_DIR}/pe_{symbol}_{today}.csv"
    if os.path.exists(cache_file):
        try:
            return float(pd.read_csv(cache_file)["pe_ttm"].iloc[0])
        except Exception:
            pass
    try:
        df = ak.stock_a_indicator_lg(symbol=symbol)
        if df is None or df.empty or "pe_ttm" not in df.columns:
            return None
        pe = df["pe_ttm"].iloc[-1]
        if pd.isna(pe):
            return None
        pe = float(pe)
        pd.DataFrame({"pe_ttm": [pe]}).to_csv(cache_file, index=False)
        return pe
    except Exception as e:
        print("PE获取失败", e)
        return None
