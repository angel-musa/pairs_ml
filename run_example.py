import pandas as pd
from core.data_loader import load_price_csv, align_pairs
from core.coint import engle_granger
from core.signal import zscore, mean_reversion_signals, compute_spread
from core.backtester import backtest_spread_strategy
from core.metrics import summarize_performance

def main():
    # 1. Load Data
    print("Loading data...")
    try:
        df = load_price_csv("data/prices.csv", date_col="date")
    except FileNotFoundError:
        print("data/prices.csv not found. Generating dummy data...")
        import numpy as np
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", periods=200, freq="B")
        aaa = np.cumsum(np.random.randn(200)) + 100
        bbb = 1.5 * aaa + 5 + np.random.randn(200) * 2
        df_gen = pd.DataFrame({"date": dates, "AAA": aaa, "BBB": bbb})
        import os
        os.makedirs("data", exist_ok=True)
        df_gen.to_csv("data/prices.csv", index=False)
        df = load_price_csv("data/prices.csv", date_col="date")

    # 2. Align Pairs
    tickers = ["AAA", "BBB"]
    # Check if tickers exist
    if not all(t in df.columns for t in tickers):
        print(f"Error: Tickers {tickers} not found in data columns: {df.columns}")
        return

    df_pairs = align_pairs(df, tickers)
    print(f"Loaded {len(df_pairs)} rows for {tickers}")
    
    # 3. Cointegration Test
    print("Running Cointegration Test...")
    # We regress BBB on AAA or AAA on BBB. Let's do BBB = a + b*AAA
    y = df_pairs["BBB"]
    x = df_pairs["AAA"]
    
    eg_res = engle_granger(y, x)
    print(f"Hedge Ratio: {eg_res.hedge_ratio:.4f}")
    print(f"Intercept: {eg_res.intercept:.4f}")
    print(f"ADF Stat: {eg_res.adf_stat:.4f}")
    print(f"p-value: {eg_res.adf_pvalue:.4f}")
    
    # 4. Generate Signals
    print("Generating Signals...")
    # Spread is already in eg_res, but let's recompute to show usage
    spread = compute_spread(y, x, eg_res.hedge_ratio, eg_res.intercept)
    z = zscore(spread, window=30) # shorter window for this small example
    signals = mean_reversion_signals(z, entry_z=1.5, exit_z=0.5)
    
    # 5. Backtest
    print("Backtesting...")
    # We trade 1 unit of spread. 
    # PnL will be in absolute dollars per 1 unit.
    bt_res = backtest_spread_strategy(spread, signals, notional=1.0)
    
    # 6. Metrics
    # To get realistic returns, we need to divide PnL by the capital required.
    # Approximate Capital = Price_Y + Hedge_Ratio * Price_X (Gross Market Value)
    # We'll use the mean prices for a static estimate.
    avg_capital = y.mean() + eg_res.hedge_ratio * x.mean()
    print(f"Estimated Capital per unit: ${avg_capital:.2f}")
    
    # Re-calculate percentage returns based on capital
    real_returns = bt_res.pnl / avg_capital
    
    summary = summarize_performance(real_returns, bt_res.turnover)
    print("\nPerformance Summary:")
    print(summary)


if __name__ == "__main__":
    main()
