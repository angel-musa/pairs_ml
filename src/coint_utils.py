# coint_utils.py
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint

def test_cointegration_fullsample(y, x):
    _, p, _ = coint(y, x)
    X = sm.add_constant(x.values)
    beta = float(sm.OLS(y.values, X).fit().params[1])
    return beta, p

def rolling_coint_pvalues(y, x, window=252) -> pd.Series:
    p = pd.Series(index=y.index, dtype=float)
    for i in range(window, len(y)):
        try:
            p.iloc[i] = coint(y.iloc[i-window:i], x.iloc[i-window:i])[1]
        except Exception:
            p.iloc[i] = np.nan
    return p

def calculate_spread_and_z(y, x, beta, window=60):
    if isinstance(beta, pd.Series):
        spread = y - beta.reindex(y.index)*x
    else:
        spread = y - float(beta)*x
    mu = spread.rolling(window, min_periods=window).mean()
    sd = spread.rolling(window, min_periods=window).std(ddof=0).replace(0, np.nan)
    z = (spread - mu)/sd
    return spread, z

def half_life(spread):
    s = spread.dropna()
    if len(s)<50: return np.inf
    s_lag = s.shift(1).dropna()
    ds = (s - s_lag).dropna()
    s_lag = s_lag.loc[ds.index]
    X = sm.add_constant(s_lag.values)
    phi = float(sm.OLS(ds.values, X).fit().params[1])
    return np.inf if phi>=0 else float(-np.log(2)/phi)
