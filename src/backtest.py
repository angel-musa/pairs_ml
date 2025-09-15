# backtest.py
import numpy as np
import pandas as pd

def backtest(y, x, beta, pred_next_dS, z, *,
             entry_z=1.5, exit_z=0.0, cost_per_leg=0.0002, z_window=60,
             coint_mask=None, time_stop=0, vol_target=False, vol_window=20,
             z_cap=3.0, meta_proba=None, meta_threshold=0.5):
    """
    If meta_proba is provided, only open NEW positions when meta_proba[t] >= meta_threshold.
    """
    # realized spread
    if isinstance(beta, pd.Series):
        S = y - beta.reindex(y.index)*x
    else:
        S = y - float(beta)*x

    # reconstruct predicted next spread: S_{t+1|t} = S_t + ΔŜ_{t+1}
    pred_next_S = S.reindex(pred_next_dS.index) + pred_next_dS

    mu = S.rolling(z_window, min_periods=z_window).mean()
    sd = S.rolling(z_window, min_periods=z_window).std(ddof=0).replace(0, np.nan)
    pred_z = (pred_next_S - mu) / sd

    idx = y.index.intersection(x.index).intersection(z.index).intersection(pred_z.index)
    z, pred_z = z.loc[idx], pred_z.loc[idx]
    y, x, S = y.loc[idx], x.loc[idx], S.loc[idx]
    valid = z.notna() & pred_z.notna()
    y, x, z, pred_z, S = y.loc[valid], x.loc[valid], z.loc[valid], pred_z.loc[valid], S.loc[valid]

    gate = pd.Series(True, index=S.index)
    if coint_mask is not None:
        gate &= coint_mask.reindex(S.index).fillna(False)
    if meta_proba is not None:
        gate &= (meta_proba.reindex(S.index).fillna(0.0) >= meta_threshold)

    y_ret = y.pct_change().fillna(0.0)
    x_ret = x.pct_change().fillna(0.0)
    leg = (y_ret - (beta.reindex(y.index)*x_ret) if isinstance(beta, pd.Series) else (y_ret - float(beta)*x_ret))

    pos = pd.Series(0, index=S.index, dtype=int)
    state, days_in_pos = 0, 0
    for t in S.index:
        if state == 0:
            days_in_pos = 0
            if gate.loc[t]:
                if pred_z.loc[t] < -entry_z: state = +1
                elif pred_z.loc[t] > +entry_z: state = -1
        else:
            days_in_pos += 1
            exit_by_z = (state>0 and z.loc[t] <= exit_z) or (state<0 and z.loc[t] >= exit_z)
            exit_by_time = (time_stop>0 and days_in_pos>=time_stop)
            if exit_by_z or exit_by_time:
                state, days_in_pos = 0, 0
        pos.loc[t] = state

    if vol_target:
        vol = leg.rolling(vol_window).std().replace(0, np.nan).fillna(method="bfill").fillna(method="ffill")
        z_mult = (pred_z.clip(-z_cap, z_cap) / z_cap)
        size = (z_mult / (vol + 1e-8)).clip(-10,10)
        pnl = pos.shift(1).fillna(0) * size.shift(1).fillna(0) * leg
    else:
        pnl = pos.shift(1).fillna(0) * leg

    trades = pos.ne(pos.shift(1)).fillna(False)
    costs = trades.astype(float) * (cost_per_leg*2)

    ret = pnl - costs
    equity = (1.0 + ret).cumprod()

    ann = 252
    sharpe = float(np.sqrt(ann) * ret.mean() / (ret.std(ddof=0) + 1e-12))
    stats = dict(
        position=pos, returns=ret, cumulative_returns=equity, pred_z=pred_z,
        trades_mask=trades, sharpe=sharpe,
        max_dd=float((equity/equity.cummax()-1.0).min()),
        hit_rate=float((ret[ret!=0]>0).mean()) if (ret!=0).any() else 0.0,
        total_return=float(equity.iloc[-1]-1.0)
    )
    return stats
