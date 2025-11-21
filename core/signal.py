import pandas as pd
import numpy as np

def compute_spread(y: pd.Series, x: pd.Series, hedge_ratio: float, intercept: float = 0.0) -> pd.Series:
    """
    spread_t = y_t - (intercept + hedge_ratio * x_t)
    """
    return y - (intercept + hedge_ratio * x)

def zscore(series: pd.Series, window: int = 60) -> pd.Series:
    """
    - Rolling mean and std.
    - Return (series - mean) / std.
    - Handle std == 0 gracefully (e.g., return NaN).
    """
    roll = series.rolling(window=window)
    mean = roll.mean()
    std = roll.std()
    
    z = (series - mean) / std
    
    # Handle std == 0 or close to 0
    # If std is 0, z will be inf or nan.
    # We can replace inf with nan.
    z = z.replace([np.inf, -np.inf], np.nan)
    
    return z

def mean_reversion_signals(z: pd.Series, entry_z: float = 2.0, exit_z: float = 0.5) -> pd.Series:
    """
    - Use a symmetric mean-reversion rule:

      Entry:
        z >  entry_z  -> short spread (signal = -1)
        z < -entry_z  -> long spread (signal =  1)

      Exit:
        |z| < exit_z  -> flat (signal = 0)

    - Positions should be held over time:
      * Use a forward-filled position series so that once entered, the position persists until exit condition.
    - Return Series of {-1, 0, 1} indexed same as z.
    """
    signals = pd.Series(np.nan, index=z.index)
    
    # Entry conditions
    signals[z > entry_z] = -1
    signals[z < -entry_z] = 1
    
    # Exit conditions
    signals[z.abs() < exit_z] = 0
    
    # Forward fill to hold positions
    signals.ffill(inplace=True)
    
    # Fill initial NaNs with 0 (flat)
    signals.fillna(0, inplace=True)
    
    return signals
