# beta_estimators.py
import numpy as np
import pandas as pd
import statsmodels.api as sm

def static_beta(y, x) -> float:
    X = sm.add_constant(x.values)
    return float(sm.OLS(y.values, X).fit().params[1])

def rolling_beta(y, x, window=120) -> pd.Series:
    cov = y.rolling(window).cov(x)
    var = x.rolling(window).var().replace(0, np.nan)
    return (cov/var).rename("beta_roll")

def rls_beta(y, x, lam=0.99) -> pd.Series:
    theta = np.array([0.0, 0.0])  # [a,b]
    P = np.eye(2)*1e6
    out = []
    xv, yv = x.fillna(method="ffill").values, y.fillna(method="ffill").values
    for xt, yt in zip(xv, yv):
        phi = np.array([1.0, xt])
        err = yt - float(phi @ theta)
        K = (P @ phi) / (lam + float(phi @ P @ phi))
        theta = theta + K*err
        P = (P - np.outer(K, phi)@P)/lam
        out.append(theta[1])
    return pd.Series(out, index=y.index, name="beta_rls")

def kalman_beta(y, x, q=1e-5, r_scale=1e-2) -> pd.Series:
    """
    Kalman filter for time-varying linear regression: y_t = a_t + b_t x_t + ε_t
    State: theta_t = [a_t, b_t];  theta_t = theta_{t-1} + w_t
    Q = q*I; R = r_scale * Var(y).  Returns series of b_t.
    """
    yv, xv = y.fillna(method="ffill").values, x.fillna(method="ffill").values
    n = len(yv)
    theta = np.zeros(2)         # [a,b]
    P = np.eye(2)*1e6
    Q = np.eye(2)*q
    r = np.var(np.diff(yv)[~np.isnan(np.diff(yv))]) * r_scale or 1e-3
    out = np.zeros(n)
    for i in range(n):
        # predict
        theta = theta            # F=I
        P = P + Q
        # update
        H = np.array([[1.0, xv[i]]])
        yhat = float(H @ theta)
        S = float(H @ P @ H.T) + r
        K = (P @ H.T) / S
        theta = theta + (K*(yv[i]-yhat)).reshape(-1)
        P = (np.eye(2) - K@H) @ P
        out[i] = theta[1]
    return pd.Series(out, index=y.index, name="beta_kalman")
