import pandas as pd
import numpy as np
from dataclasses import dataclass

@dataclass
class BacktestResult:
    pnl: pd.Series
    returns: pd.Series
    positions: pd.Series
    turnover: float

def backtest_spread_strategy(spread: pd.Series, signal: pd.Series, notional: float = 1.0) -> BacktestResult:
    """
    - Align spread and signal by index.
    - Sort by index.
    - Assume signal_t is the position used over [t, t+1).
      * So shift signal by 1 to get position_t.
    - Compute spread_diff = spread.diff().
    - pnl_t = position_t * spread_diff_t * notional.
    - returns_t = pnl_t / abs(notional).
    - turnover = sum of absolute changes in position over time.

    Return BacktestResult with all fields populated.
    """
    # Align
    df = pd.concat([spread, signal], axis=1).dropna()
    spread_aligned = df.iloc[:, 0]
    signal_aligned = df.iloc[:, 1]
    
    # Sort
    spread_aligned.sort_index(inplace=True)
    signal_aligned.sort_index(inplace=True) # Redundant if df is sorted, but safe
    
    # Position
    # signal_t is the target position at time t.
    # We assume we hold this position for the next period.
    # So the position active for the return at t is signal_{t-1}.
    positions = signal_aligned.shift(1)
    
    # Spread diff
    spread_diff = spread_aligned.diff()
    
    # PnL
    # pnl_t = pos_{t-1} * (spread_t - spread_{t-1})
    pnl = positions * spread_diff * notional
    
    # Returns
    returns = pnl / abs(notional)
    
    # Turnover
    # Sum of absolute changes in signal (trades)
    # We use the unshifted signal to see trades at time t.
    turnover = signal_aligned.diff().abs().sum()
    
    return BacktestResult(
        pnl=pnl,
        returns=returns,
        positions=positions,
        turnover=turnover
    )
