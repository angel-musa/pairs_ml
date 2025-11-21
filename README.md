# Statistical Arbitrage Research Engine

This repository contains a modular statistical arbitrage research engine for pairs trading.

## Project Structure

```text
pairs_ml/
  core/
    __init__.py
    data_loader.py
    coint.py
    signal.py
    backtester.py
    metrics.py
  notebooks/
    01_eda.ipynb
    02_coint_tests.ipynb
    03_backtest.ipynb
  data/
  run_example.py
  README.md
  requirements.txt
```

<<<<<<< HEAD
## Key Features
=======
- **Data Loading**: Daily `Adj Close` via `yfinance`.
- **Cointegration (Engle–Granger)**: Tests pair relationship and estimates hedge ratio **β** via OLS on log prices.
- **Feature Engineering (leakage-safe)**:
  - Raw and standardized **spread** (log(A) − β·log(B)), rolling **z-scores**, MAs, rolling std.
  - Returns for both assets.
  - Lagged features: 1, 2, 3, 5 periods (configurable).
  - **Target**: next-period spread (i.e., predict \( s_{t+1} \)).
- **ML Pipeline**:
  - Default: `RidgeCV` with `TimeSeriesSplit` (no look-ahead).
  - Optional: `XGBoostRegressor` (toggle in config).
  - **Walk-forward** predictions (expanding window).
- **Signals & Backtest**:
  - Convert **predicted next-period spread** to positions with configurable z-score thresholds.
  - Market-neutral: long/short legs sized by hedge ratio β.
  - Slippage/fees are configurable.
- **Metrics & Plots**:
  - CAGR, Sharpe, Sortino, max drawdown, hit rate, avg win/loss, turnover.
  - Equity curve, drawdown curve, residual diagnostics, feature importances (if XGB).
 
## Next Steps: 
- currently working with finding optimal input parameters for max returns

>>>>>>> 65161f3635bcbfd415bb415793ff90ab4885b736

*   **Cointegration Modelling**: Engle-Granger tests and rolling hedge ratios.
*   **Signal Generation**: Z-score based mean-reversion signals with entry/exit thresholds.
*   **Vectorized Backtesting**: Fast backtesting using pandas/numpy.
*   **Performance Analytics**: Sharpe ratio, max drawdown, hit rate, turnover.

## Quickstart

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the example script:
    ```bash
    python run_example.py
    ```

3.  Explore the notebooks in `notebooks/` for detailed analysis.
