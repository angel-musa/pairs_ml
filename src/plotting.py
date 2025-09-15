# plotting.py
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_results(bt, z, entry_threshold, exit_threshold, outfile=None):
    # Default: project root (parent of this file's directory)
    if outfile is None:
        outfile = Path(__file__).resolve().parents[1] / "pairs_trading_results.png"
    else:
        outfile = Path(outfile)

    fig, (ax1, ax2) = plt.subplots(2,1, figsize=(12,10))
    eq = bt["cumulative_returns"]
    ax1.plot(eq.index, eq.values, label="Equity Curve", linewidth=2)
    ax1.axhline(1.0, color="gray", ls="--", alpha=0.6)
    ax1.set_title("Equity Curve (ML Pairs)")
    ax1.set_ylabel("Cumulative Return (×)")
    ax1.grid(True, alpha=0.3); ax1.legend()

    common = bt["pred_z"].index.intersection(z.index)
    ax2.plot(bt["pred_z"].loc[common].index, bt["pred_z"].loc[common].values, label="Predicted z")
    ax2.plot(z.loc[common].index, z.loc[common].values, label="Actual z", alpha=0.6)
    ax2.axhline(entry_threshold, color="red", ls="--", alpha=0.7)
    ax2.axhline(-entry_threshold, color="red", ls="--", alpha=0.7)
    ax2.axhline(exit_threshold, color="green", ls="--", alpha=0.7)
    ax2.set_title("Predicted vs Actual z-score"); ax2.set_ylabel("z"); ax2.set_xlabel("Date")
    ax2.grid(True, alpha=0.3); ax2.legend()

    plt.tight_layout()
    plt.savefig(outfile, dpi=150, bbox_inches="tight")
    print(f"Plots saved as '{outfile}'")
    plt.close()
