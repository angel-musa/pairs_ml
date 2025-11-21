import sys
import os
import logging
import time
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Dict

# Add root directory to sys.path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_loader import load_price_csv, align_pairs
from core.coint import engle_granger
from core.signal import compute_spread, zscore, mean_reversion_signals
from core.backtester import backtest_spread_strategy
from core.metrics import summarize_performance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DEFAULT_WINDOW = 60
DEFAULT_ENTRY_Z = 2.0
DEFAULT_EXIT_Z = 0.5
MIN_WINDOW = 20
MAX_WINDOW = 252
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "prices.csv")

app = FastAPI(
    title="Statistical Arbitrage Research Engine API",
    description="REST API for running cointegration-based pairs trading backtests",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BacktestRequest(BaseModel):
    """Request model for backtest endpoint"""
    tickers: List[str]
    window: int = DEFAULT_WINDOW
    entry_z: float = DEFAULT_ENTRY_Z
    exit_z: float = DEFAULT_EXIT_Z
    notional: float = 1000.0
    
    @validator('tickers')
    def validate_tickers(cls, v):
        if len(v) != 2:
            raise ValueError('Exactly 2 tickers required')
        if v[0] == v[1]:
            raise ValueError('Tickers must be different')
        return v
    
    @validator('window')
    def validate_window(cls, v):
        if v < MIN_WINDOW:
            raise ValueError(f'Window must be >= {MIN_WINDOW}')
        if v > MAX_WINDOW:
            raise ValueError(f'Window must be <= {MAX_WINDOW}')
        return v
    
    @validator('entry_z')
    def validate_entry_z(cls, v):
        if v <= 0:
            raise ValueError('Entry Z-score must be positive')
        if v > 5:
            raise ValueError('Entry Z-score seems unreasonably high (>5)')
        return v
    
    @validator('exit_z')
    def validate_exit_z(cls, v, values):
        if v < 0:
            raise ValueError('Exit Z-score must be non-negative')
        if 'entry_z' in values and v >= values['entry_z']:
            raise ValueError('Exit Z-score must be < Entry Z-score')
        return v

class Metrics(BaseModel):
    """Performance metrics model"""
    sharpe: float
    max_drawdown: float
    hit_rate: float
    total_return: float
    turnover: float
    estimated_capital: float

class BacktestResponse(BaseModel):
    """Response model for backtest endpoint"""
    dates: List[str]
    price_y: List[float]
    price_x: List[float]
    spread: List[float]
    zscore: List[float]
    position: List[float]
    pnl: List[float]
    equity: List[float]
    metrics: Metrics
    hedge_ratio: float
    intercept: float

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Statistical Arbitrage Research Engine API",
        "version": "1.0.0"
    }

@app.get("/api/pairs")
def get_pairs():
    """
    Get list of available tickers from the data file.
    
    Returns:
        dict: JSON object with 'tickers' key containing list of available ticker symbols
    
    Raises:
        HTTPException: 404 if data file not found, 500 on other errors
    """
    logger.info("Fetching available ticker pairs")
    
    if not os.path.exists(DATA_PATH):
        logger.error(f"Data file not found at {DATA_PATH}")
        raise HTTPException(status_code=404, detail=f"Data file not found: {DATA_PATH}")
    
    try:
        df = pd.read_csv(DATA_PATH)
        cols = [c for c in df.columns if c.lower() != "date"]
        logger.info(f"Found {len(cols)} tickers: {cols}")
        return {"tickers": cols}
    except Exception as e:
        logger.error(f"Error loading ticker list: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/api/run_backtest", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest):
    """
    Run a pairs trading backtest with cointegration-based signals.
    
    Args:
        req: BacktestRequest containing tickers and parameters
        
    Returns:
        BacktestResponse with timeseries data and performance metrics
        
    Raises:
        HTTPException: 400 for invalid inputs, 500 for processing errors
    """
    start_time = time.time()
    logger.info(f"Backtest requested: {req.tickers}, window={req.window}, entry_z={req.entry_z}, exit_z={req.exit_z}")
    
    try:
        # 1. Load Data
        logger.info(f"Loading data from {DATA_PATH}")
        df = load_price_csv(DATA_PATH, date_col="date")
        
        # Validate tickers exist
        for ticker in req.tickers:
            if ticker not in df.columns:
                logger.error(f"Ticker not found: {ticker}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Ticker '{ticker}' not found in data. Available: {list(df.columns)}"
                )
        
        df_pairs = align_pairs(df, req.tickers)
        
        if df_pairs.empty:
            logger.error("No overlapping data for selected pairs")
            raise HTTPException(status_code=400, detail="No overlapping data for pairs")
        
        # Validate window size vs data length
        if len(df_pairs) < req.window:
            logger.error(f"Insufficient data: {len(df_pairs)} rows < window {req.window}")
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient data ({len(df_pairs)} rows) for window size ({req.window})"
            )
        
        y = df_pairs[req.tickers[1]]  # Dependent
        x = df_pairs[req.tickers[0]]  # Independent
        
        logger.info(f"Loaded {len(df_pairs)} rows for {req.tickers}")
        
        # 2. Cointegration
        logger.info("Running cointegration test")
        eg_res = engle_granger(y, x)
        logger.info(f"Hedge ratio: {eg_res.hedge_ratio:.4f}, ADF p-value: {eg_res.p_value:.4f}")
        
        # 3. Signals
        logger.info("Generating signals")
        spread = compute_spread(y, x, eg_res.hedge_ratio, eg_res.intercept)
        z = zscore(spread, window=req.window)
        z = z.fillna(0)  # Handle NaNs at start
        
        signals = mean_reversion_signals(z, entry_z=req.entry_z, exit_z=req.exit_z)
        
        # 4. Backtest
        logger.info("Running backtest")
        bt_res = backtest_spread_strategy(spread, signals, notional=1.0)
        
        # Calculate Capital Base (for return normalization)
        avg_capital = y.mean() + eg_res.hedge_ratio * x.mean()
        real_returns = bt_res.pnl / avg_capital
        equity_curve = (1 + real_returns.fillna(0)).cumprod()
        
        # 5. Metrics
        summary = summarize_performance(real_returns, bt_res.turnover)
        logger.info(f"Performance - Sharpe: {summary.sharpe:.2f}, Return: {summary.total_return:.2%}, MDD: {summary.max_drawdown:.2%}")
        
        # 6. Prepare response
        dates = df_pairs.index.strftime("%Y-%m-%d").tolist()
        
        def clean_series(s):
            """Replace NaN/Inf with 0 for JSON serialization"""
            return s.replace([np.inf, -np.inf], np.nan).fillna(0).tolist()
        
        elapsed = time.time() - start_time
        logger.info(f"Backtest completed successfully in {elapsed:.2f}s")
        
        return BacktestResponse(
            dates=dates,
            price_y=clean_series(y),
            price_x=clean_series(x),
            spread=clean_series(spread),
            zscore=clean_series(z),
            position=clean_series(bt_res.positions),
            pnl=clean_series(bt_res.pnl),
            equity=clean_series(equity_curve),
            metrics=Metrics(
                sharpe=float(summary.sharpe),
                max_drawdown=float(summary.max_drawdown),
                hit_rate=float(summary.hit_rate),
                total_return=float(summary.total_return),
                turnover=float(summary.turnover),
                estimated_capital=float(avg_capital)
            ),
            hedge_ratio=float(eg_res.hedge_ratio),
            intercept=float(eg_res.intercept)
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backtest processing error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000)
