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

## Key Features

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
