ML-Driven Pairs Trading (IBKR + Adaptive β + Meta-Labeling)

A compact, interview-ready quant research framework for mean-reversion pairs with a modern ML workflow:

Live IBKR data via ib_insync (with local CSV caching)

Adaptive hedge ratio β: static, rolling, rls (Recursive Least Squares), kalman

Rolling Engle–Granger cointegration gating (window & p-value thresholds)

Leakage-safe features and Δ-spread forecasting (RidgeCV or XGBoost) with purged time-series CV

Optional triple-barrier meta-labeling (probability gate on entries)

Simulator with transaction costs, volatility targeting, and time-stops

Clean, modular code; plots auto-saved to the project root

What it does (end-to-end)

Pulls daily bars for two tickers from IBKR and caches them.

Estimates hedge ratio β (static/rolling/RLS/Kalman), lagged 1 day to avoid look-ahead.

Computes spread 
𝑆
𝑡
=
𝑌
𝑡
−
𝛽
𝑡
𝑋
𝑡
S
t
	​

=Y
t
	​

−β
t
	​

X
t
	​

 and z-score on a rolling window.

Builds leakage-safe features; target is next-period Δspread.

Trains RidgeCV (default) or XGBoost with purged TimeSeriesSplit; prints RMSE vs naive baseline.

(Optional) Creates triple-barrier labels and trains a meta-classifier; only takes signals above a probability threshold.

Backtests with cointegration/meta gates, costs, vol targeting, time-stop → prints Sharpe, trades, DD, etc.

Saves equity + predicted vs actual z plot to pairs_trading_results.png in the repo root.

Project structure
pairs/
├─ data/                      # cached CSVs (auto-created)
├─ src/
│  ├─ data_loader.py          # IBKR data + cache
│  ├─ beta_estimators.py      # static / rolling / RLS / Kalman β
│  ├─ coint_utils.py          # cointegration, spread/z, half-life
│  ├─ features.py             # feature engineering (Δspread target)
│  ├─ labeling.py             # triple-barrier & meta dataset
│  ├─ models.py               # purged-CV regressors + meta-classifier
│  ├─ backtest.py             # simulator (gates, sizing, stops, costs)
│  ├─ plotting.py             # plots → ../pairs_trading_results.png
│  └─ pairs_ml.py             # main CLI
├─ requirements.txt
└─ README.md

Quick start
1) Create env & install
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

2) IBKR Paper setup

Launch TWS Paper (default port 7497) or IB Gateway

File → Global Configuration → API → Settings

✔ Enable ActiveX/Socket Clients

Add 127.0.0.1 to trusted IPs

Keep TWS running while you test.

3) Run an example
# RLS β, cointegration gate, vol targeting, meta gate (good “busy but sane” defaults)
python .\src\pairs_ml.py --tickers "XOM,CVX" --beta-mode rls --rls-lam 0.99 `
  --z-window 120 --entry-z 2.0 --exit-z 0.1 `
  --coint-window 180 --coint-threshold 0.15 `
  --time-stop 30 --vol-target --vol-window 20 --z-cap 3.0 `
  --meta --meta-pt 1.5 --meta-sl 1.0 --meta-h 20 --meta-thresh 0.55 `
  --meta-train-entry-z 1.6


Outputs

Plot: pairs_trading_results.png (repo root, one level above src/)

Console metrics: Trades, Sharpe, Total Return, Max DD, Hit Rate, signal/eligible counts, and a forward correlation diagnostic.

CLI (key flags)

Pair & dates

--tickers "AAPL,MSFT" · --start 2020-01-01 · --end 2024-12-31

β (hedge ratio)

--beta-mode {static,rolling,rls,kalman} (default rolling)

--beta-window 120 (for rolling)

--rls-lam 0.99

--kalman-q 1e-5 --kalman-r-scale 1e-2

Cointegration gate

--coint-window 180 --coint-threshold 0.15

--no-coint-gate to disable

Z logic & costs

--z-window 120

--entry-z 2.0 --exit-z 0.1

--cost-bps 2.0 (per leg)

ML models

Default RidgeCV, add --use-xgb for XGBoost

Purged time-series CV is built in

Meta-labeling (triple barrier)

Enable: --meta

Barriers: --meta-pt 1.5 --meta-sl 1.0 --meta-h 20

Probability gate: --meta-thresh 0.55

Build meta dataset with a looser entry (optional): --meta-train-entry-z 1.6
(Trading still uses --entry-z.)

Execution polishing

--vol-target --vol-window 20 --z-cap 3.0

--time-stop 30 (max holding days)

Diagnostics

Half-life printout with selectable β (does not affect trading):
--hl-beta-mode {auto,static,rolling,rls,kalman}

IBKR connection

--host 127.0.0.1 --port 7497 --client-id 11

--use-rth (regular hours) / --all-hours

--adjusted (ADJUSTED_LAST) / --raw (TRADES)

Interpreting the metrics

Trades — entries (flat → non-flat)

Hit Rate — fraction of non-zero return days that are positive (coarse proxy)

Sharpe — √252-scaled Sharpe on net daily returns (after costs)

Max Drawdown — peak-to-trough decline on the equity curve

Signal days — days with 
∣
𝑧
^
∣
∣
z
^
∣ ≥ entry; Eligible — those that also pass cointegration (and meta) gates

Corr(pred_z(t), z(t+1)) — forward correlation of level z; expect high values when z is persistent. Use PnL metrics to judge trade quality.

Tips to get more (or better) trades

Ease triggers: lower --entry-z (e.g., 1.8–2.0) or loosen --coint-threshold (0.15–0.20).

RLS β (--beta-mode rls --rls-lam 0.99) often produces responsive, tradable spreads; Kalman can over-explain co-movement (fewer z excursions).

If meta prints “dataset too small,” build it with --meta-train-entry-z 1.6–1.8, then trade at your preferred entry.

Compare half-life across β (--hl-beta-mode)—β choice strongly affects spread stationarity.

Requirements

Python 3.10+

TWS Paper / IB Gateway running with API enabled

pip install -r requirements.txt

ib_insync, pandas, numpy, matplotlib, statsmodels, scikit-learn, xgboost

Disclaimer

This repository is for research and education only. It is not investment advice. Past performance from simulations does not guarantee future results.