# labeling.py
import numpy as np
import pandas as pd

def triple_barrier_labels(series: pd.Series, vol: pd.Series,
                          pt_mult=1.5, sl_mult=1.0, max_h=20) -> pd.Series:
    """
    Labels +1 / -1 / 0 on 'series' (e.g., z or spread).
    +1 if upper barrier hit first, -1 if lower, 0 if neither within horizon.
    Barriers: s_t ± k * vol_t. Uses forward window of length max_h.
    """
    s = series
    v = vol.fillna(method="bfill").fillna(method="ffill")
    idx = s.index
    out = pd.Series(index=idx, dtype=float)

    for i, t in enumerate(idx[:-1]):
        start = s.iloc[i]; sig = v.iloc[i]
        up, dn = start + pt_mult*sig, start - sl_mult*sig
        end_i = min(i+max_h, len(idx)-1)
        w = s.iloc[i+1:end_i+1]
        if len(w)==0: break
        hit_up = (w >= up).idxmax() if (w >= up).any() else None
        hit_dn = (w <= dn).idxmax() if (w <= dn).any() else None
        if hit_up is not None and (hit_dn is None or hit_up <= hit_dn):
            out.iloc[i] = 1.0
        elif hit_dn is not None and (hit_up is None or hit_dn <= hit_up):
            out.iloc[i] = -1.0
        else:
            out.iloc[i] = 0.0
    return out

def build_meta_dataset(features: pd.DataFrame,
                        pred_z: pd.Series,
                        z: pd.Series,
                        entry_z: float,
                        vol_window: int = 20,
                        pt_mult: float = 1.5,
                        sl_mult: float = 1.0,
                        max_h: int = 20):
    """
    Build (X_meta, y_meta) for classifier using triple-barrier outcome
    ONLY on timestamps where |pred_z| >= entry_z (i.e., where you'd consider entering).
    Direction comes from sign(pred_z): long spread if pred_z < -entry, short if > +entry.
    Success = barrier in predicted direction hit first (y_meta=1), else 0.
    """
    zvol = z.diff().rolling(vol_window).std().clip(lower=1e-8)
    labels = triple_barrier_labels(z, zvol, pt_mult=pt_mult, sl_mult=sl_mult, max_h=max_h)

    # candidate signals
    candidates = pred_z.index[(pred_z <= -entry_z) | (pred_z >= entry_z)]
    X_meta = features.loc[candidates].drop(columns=["target"], errors="ignore").copy()
    # outcome aligned to the same time (uses future info for labeling, but only for training)
    lbl = labels.reindex(candidates)

    # Map sign: if predicted short (pred_z>0), success when label==-1; if long, success when label==+1
    side = np.sign(pred_z.reindex(candidates))
    y_meta = pd.Series(0, index=candidates, dtype=int)
    y_meta[(side > 0) & (lbl == -1)] = 1  # predicted short & down barrier hit
    y_meta[(side < 0) & (lbl == +1)] = 1  # predicted long & up barrier hit

    # drop NaNs
    mask = X_meta.notna().all(axis=1) & lbl.notna()
    return X_meta.loc[mask], y_meta.loc[mask]
