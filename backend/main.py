import sys
import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

# Add root directory to sys.path to import core modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_loader import load_price_csv, align_pairs
from core.coint import engle_granger
from core.signal import compute_spread, zscore, mean_reversion_signals
from core.backtester import backtest_spread_strategy
from core.metrics import summarize_performance

app = FastAPI(title="Stat Arb Research Engine API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default is 5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "prices.csv")

class BacktestRequest(BaseModel):
    tickers: List[str]
    window: int = 60
    entry_z: float = 2.0
    exit_z: float = 0.5
    notional: float = 1000.0  # Default to a reasonable amount, though we will calculate capital based returns

class BacktestResponse(BaseModel):
    dates: List[str]
    price_y: List[float]
    price_x: List[float]
    spread: List[float]
    zscore: List[float]
    position: List[float]
    pnl: List[float]
    equity: List[float]
    metrics: Dict[str, float]
    hedge_ratio: float
    intercept: float

@app.get("/api/pairs")
def get_pairs():
    if not os.path.exists(DATA_PATH):
        raise HTTPException(status_code=404, detail="Data file not found")
    
    try:
        df = pd.read_csv(DATA_PATH)
        # Exclude date column and non-numeric columns if any, but mainly just return columns
        cols = [c for c in df.columns if c.lower() != "date"]
        return {"tickers": cols}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run_backtest", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest):
    if len(req.tickers) != 2:
        raise HTTPException(status_code=400, detail="Exactly 2 tickers required")
    
    try:
        # 1. Load Data
        df = load_price_csv(DATA_PATH, date_col="date")
        df_pairs = align_pairs(df, req.tickers)
        
        if df_pairs.empty:
            raise HTTPException(status_code=400, detail="No overlapping data for pairs")
            
        y = df_pairs[req.tickers[1]] # Second ticker as Y (dependent)
        x = df_pairs[req.tickers[0]] # First ticker as X (independent) - Convention choice
        
        # 2. Cointegration
        eg_res = engle_granger(y, x)
        
        # 3. Signals
        spread = compute_spread(y, x, eg_res.hedge_ratio, eg_res.intercept)
        z = zscore(spread, window=req.window)
        # Handle NaNs in z (start of window)
        z = z.fillna(0)
        
        signals = mean_reversion_signals(z, entry_z=req.entry_z, exit_z=req.exit_z)
        
        # 4. Backtest
        # We use notional=1.0 to get raw PnL per unit of spread, then normalize by capital
        bt_res = backtest_spread_strategy(spread, signals, notional=1.0)
        
        # Calculate Capital Base
        # Capital = Price_Y + Hedge_Ratio * Price_X
        # We use a rolling estimate or static mean. Let's use static mean for simplicity as per example
        avg_capital = y.mean() + eg_res.hedge_ratio * x.mean()
        
        # Normalize PnL to Returns
        real_returns = bt_res.pnl / avg_capital
        
        # Equity Curve
        equity_curve = (1 + real_returns.fillna(0)).cumprod()
        
        # 5. Metrics
        summary = summarize_performance(real_returns, bt_res.turnover)
        
        # Prepare response
        # Convert index to string dates
        dates = df_pairs.index.strftime("%Y-%m-%d").tolist()
        
        # Helper to replace NaNs/Infs for JSON
        def clean_series(s):
            return s.replace([np.inf, -np.inf], np.nan).fillna(0).tolist()

        return {
            "dates": dates,
            "price_y": clean_series(y),
            "price_x": clean_series(x),
            "spread": clean_series(spread),
            "zscore": clean_series(z),
            "position": clean_series(bt_res.positions),
            "pnl": clean_series(bt_res.pnl), # Raw PnL
            "equity": clean_series(equity_curve),
            "metrics": {
                "sharpe": float(summary.sharpe),
                "max_drawdown": float(summary.max_drawdown),
                "hit_rate": float(summary.hit_rate),
                "total_return": float(summary.total_return),
                "turnover": float(summary.turnover),
                "estimated_capital": float(avg_capital)
            },
            "hedge_ratio": float(eg_res.hedge_ratio),
            "intercept": float(eg_res.intercept)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
