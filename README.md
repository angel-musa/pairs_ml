# Statistical Arbitrage Research Engine

> A statistical arbitrage research platform for cointegration-based pairs trading with an interactive web dashboard for running backtests and visualizing performance.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-blue.svg)](https://reactjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

This project provides a complete statistical arbitrage research framework designed for quantitative analysts and algorithmic traders. It implements a **cointegration-based pairs trading strategy** with a full-stack web interface for experimentation and visualization.

The system consists of three main components:
1. **Core Research Engine**: Modular Python library for cointegration testing, signal generation, backtesting, and performance analytics
2. **FastAPI Backend**: REST API exposing the research engine for web consumption
3. **React Frontend**: Interactive dashboard with real-time charting and parameter controls

## Why This Project Exists

This project demonstrates:
- **Quantitative Research Skills**: Implementation of Engle-Granger cointegration, z-score based mean-reversion signals, and vectorized backtesting
- **Full-Stack Engineering**: Clean separation of concerns between research code, API layer, and user interface
- **Production-Ready Practices**: Type hints, modular architecture, comprehensive documentation, and testability
- **Financial Domain Knowledge**: Understanding of pairs trading mechanics, risk metrics (Sharpe, drawdown), and market-neutral strategies

Perfect for showcasing to quant recruiters, this repository bridges the gap between academic research and production systems.

## Features

### Core Engine
- **Engle-Granger Cointegration**: Statistical tests for identifying cointegrated pairs
- **Rolling Hedge Ratios**: Dynamic calculation of optimal hedge ratios using rolling OLS
- **Z-Score Signals**: Mean-reversion entry/exit signals with configurable thresholds
- **Vectorized Backtesting**: Fast NumPy-based backtesting engine
- **Performance Metrics**: Sharpe ratio, maximum drawdown, hit rate, turnover, total return

### Web Application
- **Interactive Dashboard**: Dark-themed UI with purple accents for professional appearance
- **Real-Time Charting**: Price series, spread/z-score, and equity curve visualization using Recharts
- **Parameter Tuning**: Adjustable window size, entry/exit thresholds with live tooltips
- **Responsive Design**: Works across desktop and tablet devices

## Project Structure

```
<<<<<<< HEAD
pairs_ml/
├── core/                    # Research engine (importable library)
│   ├── __init__.py         # Public API exports
│   ├── data_loader.py      # CSV loading and data alignment
│   ├── coint.py            # Cointegration tests and hedge ratios
│   ├── signal.py           # Spread calculation and signal generation
│   ├── backtester.py       # Vectorized backtesting logic
│   └── metrics.py          # Performance analytics
├── backend/                 # FastAPI web server
│   ├── main.py             # API endpoints and business logic
│   ├── requirements.txt    # Backend Python dependencies
│   └── tests/              # Backend test suite
├── frontend/                # React + TypeScript dashboard
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── lib/            # API client
│   │   └── App.tsx         # Main application
│   ├── package.json
│   └── ...
├── notebooks/               # Jupyter notebooks for research
│   ├── 01_eda.ipynb
│   ├── 02_coint_tests.ipynb
│   └── 03_backtest.ipynb
├── data/                    # Price data (CSV format)
│   └── prices.csv          # Sample cointegrated series
├── run_example.py          # Standalone demo script
├── requirements.txt        # Core engine dependencies
└── README.md
```
=======

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
- currently working with finding optimal input parameters for max returns (ml model integration)

*   **Cointegration Modelling**: Engle-Granger tests and rolling hedge ratios.
*   **Signal Generation**: Z-score based mean-reversion signals with entry/exit thresholds.
*   **Vectorized Backtesting**: Fast backtesting using pandas/numpy.
*   **Performance Analytics**: Sharpe ratio, max drawdown, hit rate, turnover.
>>>>>>> 5f90026874eeefb6fcbb8f2a01fd84c753cfd1b2

## Quickstart

### 1. Engine-Only Demo

Run the core engine without the web interface:

```bash
# Install dependencies
pip install -r requirements.txt

# Run example backtest
python run_example.py
```

This will:
- Load sample price data from `data/prices.csv`
- Test for cointegration between ticker pairs
- Generate mean-reversion signals
- Run a backtest and print performance metrics

### 2. Full Web Application

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Documentation: `http://localhost:8000/docs`

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

#### Using the Dashboard

1. Select two tickers from the dropdowns (e.g., AAA, BBB)
2. Configure parameters:
   - **Rolling Window**: Number of days for z-score calculation (default: 60)
   - **Entry Z-Score**: Threshold to enter positions (default: 2.0)
   - **Exit Z-Score**: Threshold to exit positions (default: 0.5)
3. Click "Run Backtest" to execute and visualize results
4. Hover over chart elements for detailed tooltips

## API Reference

### POST `/api/run_backtest`

Run a pairs trading backtest with specified parameters.

**Request Body:**
```json
{
  "tickers": ["AAA", "BBB"],
  "window": 60,
  "entry_z": 2.0,
  "exit_z": 0.5,
  "notional": 1.0
}
```

**Response:**
```json
{
  "dates": ["2020-01-01", ...],
  "price_y": [100.5, ...],
  "price_x": [50.2, ...],
  "spread": [0.15, ...],
  "zscore": [1.2, ...],
  "position": [0, 1, 1, -1, ...],
  "equity": [1.0, 1.02, 1.05, ...],
  "metrics": {
    "sharpe": 1.45,
    "total_return": 0.15,
    "max_drawdown": -0.08,
    "hit_rate": 0.62,
    "turnover": 24,
    "estimated_capital": 150.5
  }
}
```

## Examples

### Dashboard Screenshot
![Dashboard](docs/img/dashboard.png)
*Interactive pairs trading dashboard with real-time charting*

### Notebook Analysis
![Backtest Notebook](docs/img/notebook_backtest.png)
*Jupyter notebook showing cointegration analysis and backtest results*

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Core engine tests (if added)
pytest core/tests/ -v
```

### Code Quality

- **Type Hints**: All public functions include comprehensive type annotations
- **Docstrings**: NumPy-style docstrings for all modules and functions
- **Linting**: Code follows PEP 8 standards
- **Modular Design**: Clean separation between data, logic, and presentation layers

## Dependencies

### Core Engine
- `numpy` - Numerical computations
- `pandas` - Data manipulation
- `scipy` - Statistical functions
- `statsmodels` - Econometric models (cointegration tests)

### Backend
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

### Frontend
- `react` - UI framework
- `typescript` - Type safety
- `recharts` - Charting library
- `tailwindcss` - Styling

## Configuration

Default parameters can be configured in environment variables or a config file:

```python
# Example: .env or config.py
DEFAULT_WINDOW = 60
DEFAULT_ENTRY_Z = 2.0
DEFAULT_EXIT_Z = 0.5
DATA_PATH = "data/prices.csv"
```

## Roadmap / TODOs

- [ ] Add parameter sweep / heatmap analysis notebook
- [ ] Implement regime-based performance segmentation
- [ ] Add transaction cost modeling
- [ ] Expand to multi-pair portfolios
- [ ] Deploy to cloud (AWS/GCP) with Docker
- [ ] Add real-time data integration

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Contact

**Project Link**: [https://github.com/angel-musa/pairs_ml](https://github.com/angel-musa/pairs_ml)

---

## Archive: Prior ML Version

An earlier version of this project explored supervised learning approaches (RidgeCV, XGBoost) for predicting spread movements. This has been superseded by the current rule-based z-score strategy for clarity and interpretability. The ML approach may be revisited in future iterations.
