# ML-Driven Pairs Trading (AAPL/MSFT)

A compact, interview-ready project that implements an **ML-driven pairs trading strategy** for cointegrated pairs. The system predicts next-period spread movements using machine learning and converts them into trading signals with proper backtesting and performance metrics.

## What it does

- **Data Loading**: Downloads daily adjusted close prices via `yfinance`
- **Cointegration Testing**: Engle-Granger test to verify pair relationship and estimate hedge ratio (β)
- **Feature Engineering**: Creates leakage-safe features including:
  - Spread, z-scores, moving averages
  - Returns for both assets
  - Lagged features (1, 2, 3, 5 periods)
  - Target: next-period spread
- **ML Pipeline**: 
  - Default: RidgeCV with TimeSeriesSplit cross-validation
  - Optional: XGBoost regressor (toggle with `USE_XGB=True`)
  - Walk-forward predictions to avoid look-ahead bias
- **Backtesting**: 
  - Converts predicted spread → predicted z-score
  - Entry: |predicted z| > 1.5, Exit: z crosses 0
  - PnL = position × (y_return - β × x_return)
  - Simple costs: 2 bps per leg on position flips
- **Performance Metrics**: Sharpe ratio, cumulative return, max drawdown, hit rate
- **Visualization**: Equity curve and predicted vs actual z-scores

## How to run

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the strategy
python pairs_ml.py
```

## Configuration

Key parameters at the top of `pairs_ml.py`:

```python
TICKER_Y = 'AAPL'        # Asset to trade
TICKER_X = 'MSFT'        # Hedge asset  
START_DATE = '2020-01-01'
ENTRY_THRESHOLD = 1.5    # |z-score| for entry
EXIT_THRESHOLD = 0.0     # z-score for exit
COST_PER_LEG = 0.0002    # 2 bps per leg
USE_XGB = False          # Toggle XGBoost vs Ridge
```

### Toggling XGBoost

To use XGBoost instead of Ridge regression:
```python
USE_XGB = True  # Change this in pairs_ml.py
```

## Default Settings

- **Pair**: AAPL/MSFT (easily changeable)
- **Period**: 2020-2024 (5 years of data)
- **Model**: RidgeCV with 5-fold TimeSeriesSplit
- **Entry**: |predicted z| > 1.5
- **Exit**: z-score crosses 0
- **Costs**: 2 bps per leg (4 bps round-trip)
- **Z-score window**: 60 days rolling

## Ideas for Extensions

- **Command-line interface**: Add argparse for tickers, dates, thresholds
- **Streamlit dashboard**: Create `streamlit_app.py` for interactive visualization
- **Configuration file**: Move parameters to `config.yaml`
- **Additional features**: Technical indicators, volatility measures, sector ETFs
- **Risk management**: Position sizing, stop-losses, portfolio-level risk
- **Alternative models**: LSTM, Random Forest, ensemble methods
- **Multiple pairs**: Portfolio of cointegrated pairs
- **Real-time trading**: Integration with broker APIs
- **Advanced costs**: Slippage, market impact, borrowing costs

## File Structure

```
pairs/
├── pairs_ml.py          # Main strategy implementation (~400 lines)
├── requirements.txt     # Pinned dependencies
├── README.md           # This file
├── .gitignore          # Git ignore rules
└── data/               # Data directory (auto-created)
    └── .gitkeep        # Keep directory in git
```

## Dependencies

All dependencies are pinned to stable versions:
- `pandas==2.2.2` - Data manipulation
- `numpy==1.26.4` - Numerical computing  
- `yfinance==0.2.52` - Yahoo Finance data
- `scikit-learn==1.5.1` - Machine learning
- `statsmodels==0.14.2` - Statistical models
- `matplotlib==3.9.0` - Plotting
- `xgboost==2.1.1` - Gradient boosting (optional)

## Interview Notes

This implementation demonstrates:
- **Data Science**: Time series analysis, cointegration testing, feature engineering
- **Machine Learning**: Cross-validation, walk-forward analysis, model comparison
- **Quantitative Finance**: Pairs trading, backtesting, performance metrics
- **Software Engineering**: Clean code structure, configuration management, error handling
- **Risk Management**: Transaction costs, position sizing, drawdown analysis

The code is designed to be easily explainable in technical interviews while showcasing both ML and quantitative finance knowledge.