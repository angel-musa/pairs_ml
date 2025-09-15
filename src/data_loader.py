# data_loader.py
import os, math
import pandas as pd
from ib_insync import IB, Stock, util

def _cache_path(cache_dir, ticker, start_date, end_date):
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{ticker}_{start_date}_{end_date}.csv")

def _ib_connect(host: str, port: int, client_id: int):
    ib = IB()
    ib.connect(host, port, clientId=client_id, readonly=True, timeout=5)
    return ib

def _ib_duration_str(start_date: str, end_date: str) -> str:
    s = pd.Timestamp(start_date)
    e = pd.Timestamp(end_date) if end_date else pd.Timestamp.today()
    yrs = max(1, math.ceil(max(1,(e-s).days)/365))
    return f"{yrs} Y"

def _ib_fetch_series(ib: IB, ticker: str, start_date: str, end_date: str,
                     adjusted: bool = True, use_rth: bool = True) -> pd.Series:
    contract = Stock(ticker, "SMART", "USD")
    what = "ADJUSTED_LAST" if adjusted else "TRADES"
    end_str = "" if adjusted else pd.Timestamp(end_date).strftime("%Y%m%d %H:%M:%S")
    bars = ib.reqHistoricalData(
        contract, endDateTime=end_str, durationStr=_ib_duration_str(start_date,end_date),
        barSizeSetting="1 day", whatToShow=what, useRTH=use_rth, formatDate=1, keepUpToDate=False
    )
    if not bars and adjusted:
        end_str = pd.Timestamp(end_date).strftime("%Y%m%d %H:%M:%S")
        bars = ib.reqHistoricalData(
            contract, endDateTime=end_str, durationStr=_ib_duration_str(start_date,end_date),
            barSizeSetting="1 day", whatToShow="TRADES", useRTH=use_rth, formatDate=1, keepUpToDate=False
        )
        if not bars:
            raise RuntimeError(f"No historical data for {ticker}")
    df = util.df(bars)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    s = df.set_index("date")["close"].astype(float).rename("Adj Close")
    return s.loc[(s.index>=pd.Timestamp(start_date))&(s.index<=pd.Timestamp(end_date))]

def load_pair(cfg):
    y_t, x_t = cfg["ticker_y"], cfg["ticker_x"]
    start, end = cfg["start_date"], cfg["end_date"]
    y_path = _cache_path(cfg["cache_dir"], y_t, start, end)
    x_path = _cache_path(cfg["cache_dir"], x_t, start, end)

    y = x = None
    if os.path.exists(y_path) and os.path.exists(x_path):
        try:
            y = pd.read_csv(y_path, parse_dates=["Date"], index_col="Date")["Adj Close"]
            x = pd.read_csv(x_path, parse_dates=["Date"], index_col="Date")["Adj Close"]
        except Exception:
            y = x = None

    if y is None or x is None:
        ib = _ib_connect(cfg["ib_host"], cfg["ib_port"], cfg["ib_client_id"])
        try:
            y = _ib_fetch_series(ib, y_t, start, end, cfg["adjusted"], cfg["use_rth"])
            x = _ib_fetch_series(ib, x_t, start, end, cfg["adjusted"], cfg["use_rth"])
        finally:
            ib.disconnect()
        idx = y.index.intersection(x.index)
        y, x = y.loc[idx], x.loc[idx]
        if len(y)==0 or len(x)==0:
            raise ValueError("IBKR returned empty data.")
        pd.DataFrame({"Adj Close": y}).to_csv(y_path, index_label="Date")
        pd.DataFrame({"Adj Close": x}).to_csv(x_path, index_label="Date")
    return y, x
