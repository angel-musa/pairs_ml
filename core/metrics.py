import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class PerformanceSummary:
    sharpe: float
    max_drawdown: float
    hit_rate: float
    total_return: float
    turnover: float

def sharpe_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    - Annualized Sharpe with zero risk-free rate.
    - Handle edge cases where std is 0 or NaN by returning 0.0.
    """
    mean_ret = returns.mean()
    std_ret = returns.std()
    
    if pd.isna(std_ret) or std_ret == 0:
        return 0.0
        
    return (mean_ret / std_ret) * np.sqrt(periods_per_year)

def max_drawdown(equity_curve: pd.Series) -> float:
    """
    - Compute max drawdown as min((equity - cummax(equity)) / cummax(equity)).
    """
    # Ensure equity curve is valid
    if equity_curve.empty:
        return 0.0
        
    peak = equity_curve.cummax()
    drawdown = (equity_curve - peak) / peak
    return drawdown.min()

def hit_rate(returns: pd.Series) -> float:
    """
    - Fraction of non-zero returns that are positive.
    - If no non-zero returns, return 0.0.
    """
    non_zero = returns[returns != 0]
    if non_zero.empty:
        return 0.0
        
    positive = non_zero[non_zero > 0]
    return len(positive) / len(non_zero)

def summarize_performance(returns: pd.Series, turnover: float, periods_per_year: int = 252) -> PerformanceSummary:
    """
    - Build equity curve: (1 + returns).cumprod().
    - total_return = final_equity - 1.
    - Compute sharpe, max_drawdown, hit_rate.
    - Pass in known turnover.
    """
    # Handle NaNs in returns (e.g. from shift)
    clean_returns = returns.fillna(0)
    
    # Equity curve starting at 1
    equity_curve = (1 + clean_returns).cumprod()
    
    # Total return
    if equity_curve.empty:
        total_ret = 0.0
    else:
        total_ret = equity_curve.iloc[-1] - 1
    
    sharpe = sharpe_ratio(clean_returns, periods_per_year)
    md = max_drawdown(equity_curve)
    hr = hit_rate(clean_returns)
    
    return PerformanceSummary(
        sharpe=sharpe,
        max_drawdown=md,
        hit_rate=hr,
        total_return=total_ret,
        turnover=turnover
    )
