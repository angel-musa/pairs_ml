# pairs_ml.py
import argparse, warnings
warnings.filterwarnings("ignore")
import pandas as pd
from pathlib import Path

from data_loader import load_pair
from beta_estimators import static_beta, rolling_beta, rls_beta, kalman_beta
from coint_utils import (
    test_cointegration_fullsample,
    rolling_coint_pvalues,
    calculate_spread_and_z,
    half_life,
)
from features import engineer_features
from models import train_regressor, train_meta_classifier
from labeling import build_meta_dataset
from backtest import backtest
from plotting import plot_results


def parse_args():
    p = argparse.ArgumentParser(
        description="ML pairs: IBKR + Δspread + Purged CV + Adaptive β + Kalman + Meta"
    )
    # Pair & dates
    p.add_argument("--tickers", default="AAPL,MSFT")
    p.add_argument("--start", default="2020-01-01")
    p.add_argument("--end", default="2024-12-31")

    # Thresholds / z
    p.add_argument("--entry-z", type=float, default=1.5)
    p.add_argument("--exit-z", type=float, default=0.0)
    p.add_argument("--cost-bps", type=float, default=2.0)
    p.add_argument("--z-window", type=int, default=60)

    # Model choice
    p.add_argument("--use-xgb", action="store_true")

    # IBKR
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7497)
    p.add_argument("--client-id", type=int, default=11)
    p.add_argument("--use-rth", action="store_true")
    p.add_argument("--all-hours", action="store_true")
    p.add_argument("--adjusted", action="store_true")
    p.add_argument("--raw", action="store_true")

    # β & cointegration
    p.add_argument("--beta-mode", choices=["static", "rolling", "rls", "kalman"], default="rolling")
    p.add_argument("--beta-window", type=int, default=120)
    p.add_argument("--rls-lam", type=float, default=0.99)
    p.add_argument("--kalman-q", type=float, default=1e-5)
    p.add_argument("--kalman-r-scale", type=float, default=1e-2)

    p.add_argument("--coint-window", type=int, default=252)
    p.add_argument("--coint-threshold", type=float, default=0.05)
    p.add_argument("--no-coint-gate", action="store_true")

    # Execution
    p.add_argument("--time-stop", type=int, default=0)
    p.add_argument("--vol-target", action="store_true")
    p.add_argument("--vol-window", type=int, default=20)
    p.add_argument("--z-cap", type=float, default=3.0)

    # Meta-labeling (triple barrier)
    p.add_argument("--meta", action="store_true", help="Enable meta-classifier probability gate")
    p.add_argument("--meta-pt", type=float, default=1.5)
    p.add_argument("--meta-sl", type=float, default=1.0)
    p.add_argument("--meta-h", type=int, default=20)
    p.add_argument("--meta-thresh", type=float, default=0.55)
    p.add_argument(
        "--meta-train-entry-z",
        type=float,
        default=None,
        help="(Optional) looser entry z just for building the meta dataset; trading still uses --entry-z",
    )

    # Diagnostics QoL
    p.add_argument(
        "--hl-beta-mode",
        choices=["auto", "static", "rolling", "rls", "kalman"],
        default="auto",
        help="Which β to use for the half-life diagnostic (does not affect trading).",
    )

    p.add_argument("--cache-dir", default="data")
    return p.parse_args()


def choose_beta(mode, y, x, cfg):
    """Return a (possibly lagged) beta per requested mode."""
    if mode == "static":
        b, _ = test_cointegration_fullsample(y, x)
        return b
    if mode == "rolling":
        return rolling_beta(y, x, cfg["beta_window"]).shift(1)
    if mode == "rls":
        return rls_beta(y, x, lam=cfg["rls_lam"]).shift(1)
    if mode == "kalman":
        return kalman_beta(y, x, q=cfg["kalman_q"], r_scale=cfg["kalman_r_scale"]).shift(1)
    raise ValueError(f"Unknown beta mode: {mode}")


def main():
    args = parse_args()
    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    if len(tickers) != 2:
        raise SystemExit("Pass exactly two tickers, e.g. --tickers KO,PEP")

    use_rth = True if (args.use_rth or not args.all_hours) else False
    adjusted = True if (args.adjusted or not args.raw) else False

    cfg = dict(
        ticker_y=tickers[0],
        ticker_x=tickers[1],
        start_date=args.start,
        end_date=args.end,
        entry_threshold=args.entry_z,
        exit_threshold=args.exit_z,
        cost_per_leg=args.cost_bps / 1e4,
        z_window=args.z_window,
        use_xgb=args.use_xgb,
        ib_host=args.host,
        ib_port=args.port,
        ib_client_id=args.client_id,
        use_rth=use_rth,
        adjusted=adjusted,
        beta_mode=args.beta_mode,
        beta_window=args.beta_window,
        rls_lam=args.rls_lam,
        kalman_q=args.kalman_q,
        kalman_r_scale=args.kalman_r_scale,
        coint_window=args.coint_window,
        coint_threshold=args.coint_threshold,
        coint_gate=(not args.no_coint_gate),
        time_stop=args.time_stop,
        vol_target=args.vol_target,
        vol_window=args.vol_window,
        z_cap=args.z_cap,
        meta=args.meta,
        meta_pt=args.meta_pt,
        meta_sl=args.meta_sl,
        meta_h=args.meta_h,
        meta_thresh=args.meta_thresh,
        meta_train_entry_z=args.meta_train_entry_z,
        hl_beta_mode=args.hl_beta_mode,
        cache_dir=args.cache_dir,
    )

    print("=" * 60)
    print("ML-Driven Pairs (IBKR) — ΔSpread + Purged CV + Adaptive β + Kalman + Meta")
    print("=" * 60)
    print(
        f"Pair: {cfg['ticker_y']}/{cfg['ticker_x']}   Dates: {cfg['start_date']} → {cfg['end_date']}"
    )
    print(
        f"EntryZ={cfg['entry_threshold']} ExitZ={cfg['exit_threshold']} Zwin={cfg['z_window']}  Cost/leg={cfg['cost_per_leg']*1e4:.1f} bps"
    )
    print(
        f"β mode: {cfg['beta_mode']} (win={cfg['beta_window']} λ={cfg['rls_lam']} q={cfg['kalman_q']} rS={cfg['kalman_r_scale']})"
    )
    print(
        f"Coint gate: {'ON' if cfg['coint_gate'] else 'OFF'} (win={cfg['coint_window']} p≤{cfg['coint_threshold']})"
    )
    print(
        f"Time stop: {cfg['time_stop']}  Vol targeting: {'ON' if cfg['vol_target'] else 'OFF'}"
    )
    print(
        f"Meta: {'ON' if cfg['meta'] else 'OFF'} (pt={cfg['meta_pt']} sl={cfg['meta_sl']} H={cfg['meta_h']} thr={cfg['meta_thresh']} train_entry={cfg['meta_train_entry_z']})"
    )
    print(
        f"Half-life diagnostic β: {cfg['hl_beta_mode']} (does not affect trading)"
    )
    print(
        f"IB: {cfg['ib_host']}:{cfg['ib_port']} RTH={'Yes' if cfg['use_rth'] else 'All'} Adjusted={'Yes' if cfg['adjusted'] else 'Raw'}"
    )
    print(f"Cache: {cfg['cache_dir']}")

    # 1) Data
    print("\nStep 1: Loading data (IBKR)...")
    y, x = load_pair(cfg)
    print(f"Loaded {len(y)} trading days.")

    # 2) Full-sample static β (diag)
    beta_static, p_full = test_cointegration_fullsample(y, x)
    print(f"\nFull-sample cointegration p={p_full:.4f}  |  static β={beta_static:.4f}")

    # 3) Trading β (lagged where applicable)
    if cfg["beta_mode"] == "static":
        print("Using static β for trading...")
        beta = beta_static
    elif cfg["beta_mode"] == "rolling":
        print("Estimating rolling β for trading...")
        beta = rolling_beta(y, x, cfg["beta_window"]).shift(1)
    elif cfg["beta_mode"] == "rls":
        print("Estimating RLS β for trading...")
        beta = rls_beta(y, x, lam=cfg["rls_lam"]).shift(1)
    else:
        print("Estimating Kalman β for trading...")
        beta = kalman_beta(y, x, q=cfg["kalman_q"], r_scale=cfg["kalman_r_scale"]).shift(1)

    # 4) Rolling cointegration gate (lagged)
    if cfg["coint_gate"]:
        print("Computing rolling cointegration p-values...")
        p_roll = rolling_coint_pvalues(y, x, cfg["coint_window"]).shift(1)
        coint_mask = (p_roll <= cfg["coint_threshold"])
        print(f"Gate true ~{100 * coint_mask.dropna().mean():.1f}% of days.")
    else:
        coint_mask = None

    # 5) Spread & z for TRADING
    print("\nStep 3: Spread & z (trading β)...")
    spread, z = calculate_spread_and_z(y, x, beta, cfg["z_window"])

    # 6) Half-life diagnostic (independent β choice)
    try:
        hl_beta_mode = cfg["hl_beta_mode"]
        if hl_beta_mode == "auto":
            hl_beta = beta  # whatever you trade with
        else:
            hl_beta = choose_beta(hl_beta_mode, y, x, cfg)
        hl_spread, _ = calculate_spread_and_z(y, x, hl_beta, cfg["z_window"])
        hl = half_life(hl_spread)
        print(f"Half-life (β={hl_beta_mode}) ≈ {hl:.1f} days")
    except Exception as e:
        print(f"(Half-life diagnostic skipped: {e})")

    # 7) Features & ΔS regressor
    print("Step 4: Features & ΔS regressor...")
    feats = engineer_features(y, x, spread, z)
    reg, pred_dS, rmse, rmse_naive = train_regressor(feats, cfg["use_xgb"])
    print(f"ΔS RMSE={rmse:.4f} | naive={rmse_naive:.4f}")

    # 8) Optional meta-classifier (triple barrier)
    meta_proba = None
    if cfg["meta"]:
        print("\nStep 5: Meta-labeling (triple barrier)...")
        # reconstruct predicted z (for dataset building only)
        pred_S = spread.reindex(pred_dS.index) + pred_dS
        mu = spread.rolling(cfg["z_window"], min_periods=cfg["z_window"]).mean()
        sd = spread.rolling(cfg["z_window"], min_periods=cfg["z_window"]).std(ddof=0).replace(0, 0.0)
        pred_z = ((pred_S - mu) / sd).reindex(pred_dS.index)

        meta_entry = cfg["meta_train_entry_z"] if cfg["meta_train_entry_z"] is not None else cfg["entry_threshold"]
        X_meta, y_meta = build_meta_dataset(
            feats.dropna(),
            pred_z.dropna(),
            z,
            entry_z=meta_entry,
            vol_window=cfg["vol_window"],
            pt_mult=cfg["meta_pt"],
            sl_mult=cfg["meta_sl"],
            max_h=cfg["meta_h"],
        )
        clf, meta_proba_in_sample = train_meta_classifier(X_meta, y_meta)
        if clf is None:
            print("Meta dataset too small — skipping meta gate.")
            meta_proba = None
        else:
            all_proba = pd.Series(index=feats.index, dtype=float)
            all_X = feats.drop(columns=["target"]).reindex(all_proba.index).dropna()
            pr = pd.Series(clf.predict_proba(all_X)[:, 1], index=all_X.index)
            meta_proba = pr
            print(f"Meta fitted. In-sample size={len(X_meta)}, positive rate={y_meta.mean():.2f}, "
                  f"train-entry-z={meta_entry}")

    # 9) Backtest
    print("\nStep 6: Backtest...")
    bt = backtest(
        y,
        x,
        beta,
        pred_dS,
        z,
        entry_z=cfg["entry_threshold"],
        exit_z=cfg["exit_threshold"],
        cost_per_leg=cfg["cost_per_leg"],
        z_window=cfg["z_window"],
        coint_mask=coint_mask,
        time_stop=cfg["time_stop"],
        vol_target=cfg["vol_target"],
        vol_window=cfg["vol_window"],
        z_cap=cfg["z_cap"],
        meta_proba=meta_proba,
        meta_threshold=cfg["meta_thresh"],
    )

    # --- RESULTS PRINTOUT (metrics & diagnostics) ---
    print("\nResults:")
    entries = int(((bt["position"] != 0) & (bt["position"].shift(1) == 0)).sum())
    print(f"  Trades: {entries}")
    print(f"  Sharpe: {bt['sharpe']:.3f}")
    print(f"  Total Return: {bt['total_return']:.3f}")
    print(f"  Max Drawdown: {bt['max_dd']:.3f}")
    print(f"  Hit Rate: {bt['hit_rate']:.3f}")

    signal_days = int((bt["pred_z"].abs() >= cfg["entry_threshold"]).sum())
    print(f"  Signal days (|pred z| ≥ {cfg['entry_threshold']}): {signal_days}")

    if coint_mask is not None:
        eligible = int(
            (
                (bt["pred_z"].abs() >= cfg["entry_threshold"])
                & (coint_mask.reindex(bt["pred_z"].index).fillna(False))
            ).sum()
        )
        print(f"  Eligible (gate & |pred z|≥entry): {eligible}")

    # Forward corr diagnostic
    aligned = pd.concat(
        [bt["pred_z"], z.shift(-1).reindex(bt["pred_z"].index)], axis=1, keys=["pred_z(t)", "z(t+1)"]
    ).dropna()
    if len(aligned) > 20:
        print(f"  Corr(pred_z(t), z(t+1)) = {aligned.corr().iloc[0,1]:.3f}")

    # 10) Plot → project root
    print("\nStep 7: Plot...")
    project_root = Path(__file__).resolve().parents[1]
    out_path = project_root / "pairs_trading_results.png"
    plot_results(bt, z, cfg["entry_threshold"], cfg["exit_threshold"], outfile=out_path)
    print("\nDone.")


if __name__ == "__main__":
    main()
