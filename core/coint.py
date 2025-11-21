import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from dataclasses import dataclass
from typing import Dict

@dataclass
class EngleGrangerResult:
    hedge_ratio: float
    intercept: float
    adf_stat: float
    adf_pvalue: float
    crit_values: Dict[str, float]
    spread: pd.Series

def engle_granger(y: pd.Series, x: pd.Series, maxlag: int = 1, regression: str = "c") -> EngleGrangerResult:
    """
    - Align y and x by index.
    - Run OLS: y_t = a + b x_t + e_t (use statsmodels OLS).
    - Compute spread = residuals = y_t - (a + b x_t).
    - Run ADF on residuals with given maxlag and regression settings.
    - Return EngleGrangerResult with hedge ratio b, intercept a, and ADF stats.
    """
    # Align
    df = pd.concat([y, x], axis=1).dropna()
    y_aligned = df.iloc[:, 0]
    x_aligned = df.iloc[:, 1]
    
    # OLS
    # statsmodels OLS requires adding constant manually if we want an intercept
    X = sm.add_constant(x_aligned)
    model = sm.OLS(y_aligned, X).fit()
    
    intercept = model.params['const']
    hedge_ratio = model.params.iloc[1] # The coefficient for x
    
    # Spread / Residuals
    # spread = y - (a + b*x)
    spread = y_aligned - (intercept + hedge_ratio * x_aligned)
    
    # ADF
    # adfuller returns: adf, pvalue, usedlag, nobs, critical values, icbest
    adf_res = adfuller(spread, maxlag=maxlag, regression=regression)
    
    return EngleGrangerResult(
        hedge_ratio=hedge_ratio,
        intercept=intercept,
        adf_stat=adf_res[0],
        adf_pvalue=adf_res[1],
        crit_values=adf_res[4],
        spread=spread
    )

def rolling_hedge_ratio(y: pd.Series, x: pd.Series, window: int = 60) -> pd.Series:
    """
    - Rolling OLS over a moving window.
    - For each window, regress y on x with intercept.
    - Return a Series of hedge ratios indexed by the window end timestamp.
    """
    # Align
    df = pd.concat([y, x], axis=1).dropna()
    y_aligned = df.iloc[:, 0]
    x_aligned = df.iloc[:, 1]
    
    from statsmodels.regression.rolling import RollingOLS
    
    X = sm.add_constant(x_aligned)
    model = RollingOLS(y_aligned, X, window=window)
    rres = model.fit()
    
    # params will have 'const' and the x column name
    # We want the coefficient for x.
    # The columns of params are usually ['const', 'name_of_x']
    # We can access by position if we are sure.
    
    return rres.params.iloc[:, 1]
