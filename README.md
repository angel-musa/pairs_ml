# ML-Driven Pairs Trading (AAPL/MSFT by default)

A compact, interview-ready project that implements an **ML-driven pairs trading strategy** for cointegrated equity pairs. The system:
1) verifies cointegration and estimates the hedge ratio (β),  
2) engineers leakage-safe time-series features,  
3) **predicts the next-period spread** using an ML model (default **RidgeCV**; optional **XGBoost**), and  
4) converts predictions into trading signals with a **walk-forward backtest** and clear **performance metrics**.

---

## ✨ What it does

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


