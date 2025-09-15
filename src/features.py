# features.py
import numpy as np
import pandas as pd

def engineer_features(y, x, spread, z):
    y_ret = y.pct_change()
    x_ret = x.pct_change()
    dS = spread.diff()

    feats = pd.DataFrame({
        "spread": spread,
        "z": z,
        "z_ma3": z.rolling(3).mean(),
        "z_ma5": z.rolling(5).mean(),
        "y_ret": y_ret,
        "x_ret": x_ret,
        "dS": dS
    })
    for lag in [1,2,3,5]:
        feats[f"z_lag{lag}"] = z.shift(lag)
        feats[f"S_lag{lag}"] = spread.shift(lag)
        feats[f"dS_lag{lag}"] = dS.shift(lag)

    # TARGET: next change in spread
    feats["target"] = dS.shift(-1)
    feats = feats.replace([np.inf,-np.inf], np.nan)
    return feats
