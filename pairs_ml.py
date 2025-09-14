"""
ML-Driven Pairs Trading Strategy (IBKR only) — CLI-enabled
- Fetches daily historical data from IBKR (TWS/Gateway) via ib_insync
- Caches to data/ to avoid repeated API calls
- Cointegration check, feature engineering, ML (Ridge/XGBoost) with walk-forward
- Simple backtest with costs; saves plots to PNG (headless-friendly)

Usage examples:
  python pairs_ml.py --tickers AAPL,MSFT --start 2020-01-01 --end 2024-12-31
  python pairs_ml.py --tickers XOM,CVX --use-xgb --entry-z 1.8 --z-window 80
  python pairs_ml.py --tickers AAPL,MSFT --port 7497 --client-id 11 --all-hours
"""

import os
import math
import argparse
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless-friendly
import matplotlib.pyplot as plt

from ib_insync import IB, Stock, util
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

from sklearn.linear_model import RidgeCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error
import xgboost as xgb


# ============================== CLI / CONFIG ===============================

def parse_args():
    p = argparse.ArgumentParser(description="ML-driven pairs trading (IBKR only)")
    p.add_argument("--tickers", type=str, default="AAPL,MSFT",
                   help="Comma-separated pair, e.g. AAPL,MSFT")
    p.add_argument("--start", type=str, default="2020-01-01",
                   help="Start date YYYY-MM-DD")
    p.add_argument("--end", type=str, default="2024-12-31",
                   help="End date YYYY-MM-DD")
    p.add_argument("--entry-z", type=float, default=1.5,
                   help="Absolute predicted z threshold to enter")
    p.add_argument("--exit-z", type=float, default=0.0,
                   help="Z level to exit (cross back through)")
    p.add_argument("--cost-bps", type=float, default=2.0,
                   help="Per-leg transaction cost in basis points")
    p.add_argument("--z-window", type=int, default=60,
                   help="Rolling window length for z-score")
    p.add_argument("--use-xgb", action="store_true",
                   help="Use XGBoostRegressor instead of RidgeCV")
    p.add_argument("--host", type=str, default="127.0.0.1",
                   help="IBKR host (default 127.0.0.1)")
    p.add_argument("--port", type=int, default=7497,
                   help="IBKR port (TWS Paper=7497, Live=7496, GW Paper=4002)")
    p.add_argument("--client-id", type=int, default=11,
                   help="IBKR clientId (any unique int)")
    group_rth = p.add_mutually_exclusive_group()
    group_rth.add_argument("--use-rth", action="store_true", help="Use Regular Trading Hours only (default)")
    group_rth.add_argument("--all-hours", action="store_true", help="Use all hours (pre/after included)")
    group_adj = p.add_mutually_exclusive_group()
    group_adj.add_argument("--adjusted", action="store_true", help="Use ADJUSTED_LAST (default)")
    group_adj.add_argument("--raw", action="store_true", help="Use TRADES (raw close)")
    p.add_argument("--cache-dir", type=str, default="data", help="Directory to cache CSVs")
    args = p.parse_args()

    # normalize flags
    use_rth = True if (args.use_rth or not args.all_hours) else False
    adjusted = True if (args.adjusted or not args.raw) else False

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if len(tickers) != 2:
        raise SystemExit("Please pass exactly two tickers via --tickers, e.g. --tickers AAPL,MSFT")

    # validate dates
    _ = pd.Timestamp(args.start)
    _ = pd.Timestamp(args.end)

    cfg = {
        "ticker_y": tickers[0],
        "ticker_x": tickers[1],
        "start_date": args.start,
        "end_date": args.end,
        "entry_threshold": float(args.entry_z),
        "exit_threshold": float(args.exit_z),
        "cost_per_leg": float(args.cost_bps) / 1e4,   # bps → decimal
        "z_window": int(args.z_window),
        "use_xgb": bool(args.use_xgb),
        "ib_host": args.host,
        "ib_port": int(args.port),
        "ib_client_id": int(args.client_id),
        "use_rth": use_rth,
        "adjusted": adjusted,
        "cache_dir": args.cache_dir
    }
    return cfg


# ============================== DATA (IBKR) ================================

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
    days = max(1, (e - s).days)
    years = max(1, math.ceil(days / 365))
    return f"{years} Y"

def _ib_fetch_series(ib: IB, ticker: str, start_date: str, end_date: str,
                     adjusted: bool = True, use_rth: bool = True) -> pd.Series:
    """
    Fetch daily closes from IBKR.
    Note: ADJUSTED_LAST does NOT support an explicit endDateTime → use '' (now) and trim locally.
    """
    contract = Stock(ticker, "SMART", "USD")
    duration = _ib_duration_str(start_date, end_date)
    what     = "ADJUSTED_LAST" if adjusted else "TRADES"

    # ADJUSTED_LAST → endDateTime must be '' (now); TRADES can use a concrete end
    end_str = "" if adjusted else pd.Timestamp(end_date).strftime("%Y%m%d %H:%M:%S")

    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end_str,
        durationStr=duration,
        barSizeSetting="1 day",
        whatToShow=what,
        useRTH=use_rth,
        formatDate=1,
        keepUpToDate=False
    )

    # Fallback to TRADES (raw) if adjusted not available
    if not bars and adjusted:
        end_str = pd.Timestamp(end_date).strftime("%Y%m%d %H:%M:%S")
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_str,
            durationStr=duration,
            barSizeSetting="1 day",
            whatToShow="TRADES",
            useRTH=use_rth,
            formatDate=1,
            keepUpToDate=False
        )
        if not bars:
            raise RuntimeError(f"IBKR returned no historical data for {ticker}")

    df = util.df(bars)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None)
    df = df.set_index("date").sort_index()
    s = df["close"].astype(float).rename("Adj Close")

    # Trim exactly to [start_date, end_date]
    s = s.loc[(s.index >= pd.Timestamp(start_date)) & (s.index <= pd.Timestamp(end_date))]
    return s

def load_data(cfg):
    """
    Load daily closes for both tickers from IBKR, with local CSV cache.
    """
    y_t, x_t = cfg["ticker_y"], cfg["ticker_x"]
    start, end = cfg["start_date"], cfg["end_date"]
    print(f"Loading IBKR data for {y_t}/{x_t} from {start} to {end}")

    y_cache = _cache_path(cfg["cache_dir"], y_t, start, end)
    x_cache = _cache_path(cfg["cache_dir"], x_t, start, end)

    y_prices = x_prices = None
    if os.path.exists(y_cache) and os.path.exists(x_cache):
        try:
            y_prices = pd.read_csv(y_cache, parse_dates=["Date"], index_col="Date")["Adj Close"]
            x_prices = pd.read_csv(x_cache, parse_dates=["Date"], index_col="Date")["Adj Close"]
        except Exception:
            y_prices = x_prices = None

    if y_prices is None or x_prices is None:
        ib = _ib_connect(cfg["ib_host"], cfg["ib_port"], cfg["ib_client_id"])
        try:
            y_prices = _ib_fetch_series(ib, y_t, start, end, cfg["adjusted"], cfg["use_rth"])
            x_prices = _ib_fetch_series(ib, x_t, start, end, cfg["adjusted"], cfg["use_rth"])
        finally:
            ib.disconnect()

        # align & cache
        idx = y_prices.index.intersection(x_prices.index)
        y_prices = y_prices.loc[idx]
        x_prices = x_prices.loc[idx]
        if len(y_prices) == 0 or len(x_prices) == 0:
            raise ValueError("No data downloaded from IBKR. Check permissions/tickers/dates.")
        pd.DataFrame({"Adj Close": y_prices}).to_csv(y_cache, index_label="Date")
        pd.DataFrame({"Adj Close": x_prices}).to_csv(x_cache, index_label="Date")

    print(f"Loaded {len(y_prices)} trading days (IBKR)")
    return y_prices, x_prices


# ========================== STATS / FEATURES ===============================

def test_cointegration(y_prices, x_prices):
    print("\nTesting cointegration...")
    _, pvalue, _ = coint(y_prices, x_prices)
    print(f"Cointegration p-value: {pvalue:.4f}")
    if pvalue < 0.05:
        print("✓ Cointegrated pair detected")
    else:
        print("⚠ Pair may not be cointegrated")

    X = sm.add_constant(x_prices.values)
    model = sm.OLS(y_prices.values, X).fit()
    beta = float(model.params[1])
    print(f"Hedge ratio (β): {beta:.4f}")
    return beta, pvalue

def calculate_spread_and_zscore(y_prices, x_prices, beta, window=60):
    spread = y_prices - beta * x_prices
    mu = spread.rolling(window, min_periods=window).mean()
    sd = spread.rolling(window, min_periods=window).std(ddof=0).replace(0, np.nan)
    z = (spread - mu) / sd
    return spread, z

def estimate_half_life(spread):
    """ΔS_t = α + φ S_{t-1} + ε; half-life = -ln(2)/φ if φ<0."""
    s = spread.dropna()
    if len(s) < 50:
        return np.inf
    s_lag = s.shift(1).dropna()
    ds = (s - s_lag).dropna()
    s_lag = s_lag.loc[ds.index]
    X = sm.add_constant(s_lag.values)
    res = sm.OLS(ds.values, X).fit()
    phi = float(res.params[1])
    if phi >= 0:
        return np.inf
    return float(-np.log(2) / phi)

def engineer_features(y_prices, x_prices, spread, z_score):
    y_ret = y_prices.pct_change()
    x_ret = x_prices.pct_change()
    spread_ret = spread.pct_change()

    z_ma3 = z_score.rolling(3).mean()
    z_ma5 = z_score.rolling(5).mean()

    features = pd.DataFrame({
        "spread": spread,
        "z_score": z_score,
        "z_ma3": z_ma3,
        "z_ma5": z_ma5,
        "y_ret": y_ret,
        "x_ret": x_ret,
        "spread_ret": spread_ret
    })
    for lag in [1, 2, 3, 5]:
        features[f"z_lag{lag}"] = z_score.shift(lag)
        features[f"spread_lag{lag}"] = spread.shift(lag)
        features[f"spread_ret_lag{lag}"] = spread_ret.shift(lag)

    features["target"] = spread.shift(-1)  # next-period spread
    features = features.replace([np.inf, -np.inf], np.nan)
    return features


# ================================ MODEL ====================================

def train_model(features, use_xgb=False):
    clean = features.dropna()
    if len(clean) < 100:
        raise ValueError("Insufficient data for training")

    X = clean.drop(columns=["target"])
    y = clean["target"]

    print(f"\nTraining model on {len(X)} samples with {X.shape[1]} features")
    tscv = TimeSeriesSplit(n_splits=5)

    if use_xgb:
        print("Using XGBoost Regressor")
        model = xgb.XGBRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9, reg_lambda=1.0,
            random_state=42, n_jobs=-1
        )
    else:
        print("Using RidgeCV")
        model = RidgeCV(alphas=np.logspace(-4, 3, 20), cv=tscv)

    preds = pd.Series(index=y.index, dtype=float)
    for tr_idx, va_idx in tscv.split(X):
        Xtr, Xva = X.iloc[tr_idx], X.iloc[va_idx]
        ytr = y.iloc[tr_idx]
        model.fit(Xtr, ytr)
        preds.iloc[va_idx] = model.predict(Xva)

    model.fit(X, y)

    # Compute RMSE on the predicted subset only (ignore leading NaNs)
    valid = preds.notna()
    rmse = float(np.sqrt(mean_squared_error(y[valid], preds[valid])))
    print(f"Model RMSE: {rmse:.4f}")
    return model, preds


# =============================== BACKTEST ===================================

def backtest_strategy(y_prices, x_prices, beta, pred_next_spread, z_score,
                      entry_threshold=1.5, exit_threshold=0.0, cost_per_leg=0.0002, z_window=60):
    print("\nBacktesting strategy...")
    print(f"Entry: |z|>{entry_threshold}, Exit at z≈{exit_threshold}, Cost per leg={cost_per_leg*1e4:.1f} bps")

    realized_spread = y_prices - beta * x_prices
    mu = realized_spread.rolling(z_window, min_periods=z_window).mean()
    sd = realized_spread.rolling(z_window, min_periods=z_window).std(ddof=0).replace(0, np.nan)
    pred_z = (pred_next_spread - mu) / sd

    # Align and drop any rows where z or pred_z are NaN (from initial window)
    idx = y_prices.index.intersection(x_prices.index).intersection(z_score.index).intersection(pred_z.index)
    y_prices = y_prices.loc[idx]
    x_prices = x_prices.loc[idx]
    z_score  = z_score.loc[idx]
    pred_z   = pred_z.loc[idx]
    valid = z_score.notna() & pred_z.notna()
    y_prices = y_prices.loc[valid]
    x_prices = x_prices.loc[valid]
    z_score  = z_score.loc[valid]
    pred_z   = pred_z.loc[valid]

    y_ret = y_prices.pct_change().fillna(0.0)
    x_ret = x_prices.pct_change().fillna(0.0)

    pos = pd.Series(0, index=y_prices.index, dtype=int)
    state = 0
    for t in y_prices.index:
        if state == 0:
            if pred_z.loc[t] < -entry_threshold:
                state = +1
            elif pred_z.loc[t] > +entry_threshold:
                state = -1
        else:
            if (state > 0 and z_score.loc[t] <= exit_threshold) or \
               (state < 0 and z_score.loc[t] >= exit_threshold):
                state = 0
        pos.loc[t] = state

    pnl = pos.shift(1).fillna(0) * (y_ret - beta * x_ret)
    trades = pos.ne(pos.shift(1)).fillna(False)
    costs = trades.astype(float) * (cost_per_leg * 2)

    ret = pnl - costs
    equity = (1.0 + ret).cumprod()

    ann = 252
    sharpe = float(np.sqrt(ann) * ret.mean() / (ret.std(ddof=0) + 1e-12))
    cumret = float(equity.iloc[-1] - 1.0)
    maxdd  = float((equity / equity.cummax() - 1.0).min())
    hitrate = float((ret[ret != 0] > 0).mean()) if (ret != 0).any() else 0.0

    print("\nBacktest Results:")
    print(f"  Trades: {int(trades.sum())}")
    print(f"  Sharpe: {sharpe:.3f}")
    print(f"  Total Return: {cumret:.3f}")
    print(f"  Max Drawdown: {maxdd:.3f}")
    print(f"  Hit Rate: {hitrate:.3f}")
    print(f"  Beta used: {beta:.4f}")

    return {
        "position": pos,
        "pnl": pnl,
        "costs": costs,
        "returns": ret,
        "cumulative_returns": equity,
        "pred_z": pred_z,
        "trades_mask": trades,
        "sharpe": sharpe,
        "max_dd": maxdd,
        "hit_rate": hitrate,
        "total_return": cumret
    }


# ================================ PLOTS =====================================

def plot_results(backtest_results, z_score, entry_threshold, exit_threshold):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    eq = backtest_results["cumulative_returns"]
    ax1.plot(eq.index, eq.values, label="Equity Curve", linewidth=2)
    ax1.axhline(1.0, color="black", linestyle="--", alpha=0.5)
    ax1.set_title("Equity Curve (ML Pairs)")
    ax1.set_ylabel("Cumulative Return (×)")
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    common = backtest_results["pred_z"].index.intersection(z_score.index)
    ax2.plot(backtest_results["pred_z"].loc[common].index,
             backtest_results["pred_z"].loc[common].values,
             label="Predicted z", alpha=0.8)
    ax2.plot(z_score.loc[common].index, z_score.loc[common].values,
             label="Actual z", alpha=0.5)
    ax2.axhline(entry_threshold, color="red", linestyle="--", alpha=0.7, label=f"Entry ±{entry_threshold}")
    ax2.axhline(-entry_threshold, color="red", linestyle="--", alpha=0.7)
    ax2.axhline(exit_threshold, color="green", linestyle="--", alpha=0.7, label=f"Exit {exit_threshold}")
    ax2.set_title("Predicted vs Actual z-score")
    ax2.set_ylabel("z")
    ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3)
    ax2.legend()

    plt.tight_layout()
    plt.savefig("pairs_trading_results.png", dpi=150, bbox_inches="tight")
    print("Plots saved as 'pairs_trading_results.png'")
    plt.close()


# ================================= MAIN =====================================

def main():
    cfg = parse_args()

    print("=" * 60)
    print("ML-Driven Pairs Trading Strategy (IBKR only, CLI)")
    print("=" * 60)
    print(f"Pair: {cfg['ticker_y']}/{cfg['ticker_x']}")
    print(f"Dates: {cfg['start_date']} → {cfg['end_date']}")
    print(f"EntryZ={cfg['entry_threshold']} ExitZ={cfg['exit_threshold']} Zwin={cfg['z_window']}  Cost/leg={cfg['cost_per_leg']*1e4:.1f} bps")
    print(f"Model: {'XGBoost' if cfg['use_xgb'] else 'RidgeCV'}")
    print(f"IB: {cfg['ib_host']}:{cfg['ib_port']} clientId={cfg['ib_client_id']}  RTH={'Yes' if cfg['use_rth'] else 'All hours'}  Adjusted={'Yes' if cfg['adjusted'] else 'Raw'}")
    print(f"Cache: {cfg['cache_dir']}")

    try:
        print("Step 1: Loading data (IBKR)...")
        y_prices, x_prices = load_data(cfg)

        print("Step 2: Testing cointegration...")
        beta, pvalue = test_cointegration(y_prices, x_prices)

        print("Step 3: Calculating spread and z-score...")
        spread, z_score = calculate_spread_and_zscore(y_prices, x_prices, beta, cfg["z_window"])

        print("Step 4: Estimating half-life...")
        half_life = estimate_half_life(spread)
        print(f"Estimated half-life: {half_life:.1f} days")

        print("Step 5: Engineering features...")
        features = engineer_features(y_prices, x_prices, spread, z_score)

        print("Step 6: Training model...")
        _, predictions = train_model(features, cfg["use_xgb"])

        print("Step 7: Backtesting strategy...")
        bt = backtest_strategy(
            y_prices, x_prices, beta, predictions, z_score,
            entry_threshold=cfg["entry_threshold"],
            exit_threshold=cfg["exit_threshold"],
            cost_per_leg=cfg["cost_per_leg"],
            z_window=cfg["z_window"]
        )

        print("Step 8: Creating plots...")
        plot_results(bt, z_score, cfg["entry_threshold"], cfg["exit_threshold"])

        print("\n" + "=" * 60)
        print("Strategy completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("Strategy failed. Check the error above.")
        print("=" * 60)


if __name__ == "__main__":
    main()
