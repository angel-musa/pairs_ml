"""
Configuration module for Statistical Arbitrage Research Engine

This module centralizes all default parameters and configuration values
used across the research engine, backend API, and example scripts.

Environment Variables (optional overrides):
    STATARB_DATA_PATH: Path to price data CSV file
    STATARB_DEFAULT_WINDOW: Default rolling window size
    STATARB_DEFAULT_ENTRY_Z: Default entry z-score threshold
    STATARB_DEFAULT_EXIT_Z: Default exit z-score threshold
"""

import os
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_DATA_PATH = DATA_DIR / "prices.csv"

# Override with environment variable if set
DATA_PATH = os.getenv("STATARB_DATA_PATH", str(DEFAULT_DATA_PATH))

# Signal Generation Parameters
DEFAULT_WINDOW = int(os.getenv("STATARB_DEFAULT_WINDOW", "60"))
DEFAULT_ENTRY_Z = float(os.getenv("STATARB_DEFAULT_ENTRY_Z", "2.0"))
DEFAULT_EXIT_Z = float(os.getenv("STATARB_DEFAULT_EXIT_Z", "0.5"))

# Validation Constraints
MIN_WINDOW = 20  # Minimum rolling window size
MAX_WINDOW = 252  # Maximum rolling window size (1 trading year)
MIN_ENTRY_Z = 0.5  # Minimum entry threshold
MAX_ENTRY_Z = 5.0  # Maximum entry threshold
MIN_EXIT_Z = 0.0  # Minimum exit threshold

# Backtesting
DEFAULT_NOTIONAL = 1000.0  # Default position size for backtesting

# Display / Formatting
DECIMAL_PLACES = {
    'sharpe': 2,
    'return': 4,
    'drawdown': 4,
    'hit_rate': 4,
    'hedge_ratio': 4,
    'z_score': 3
}

# Logging
LOG_LEVEL = os.getenv("STATARB_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_config_summary() -> dict:
    """
    Get a summary of current configuration.
    
    Returns:
        dict: Configuration parameters
    """
    return {
        "data_path": DATA_PATH,
        "default_params": {
            "window": DEFAULT_WINDOW,
            "entry_z": DEFAULT_ENTRY_Z,
            "exit_z": DEFAULT_EXIT_Z,
            "notional": DEFAULT_NOTIONAL
        },
        "constraints": {
            "min_window":MIN_WINDOW,
            "max_window": MAX_WINDOW,
            "min_entry_z": MIN_ENTRY_Z,
            "max_entry_z": MAX_ENTRY_Z,
            "min_exit_z": MIN_EXIT_Z
        }
    }

if __name__ == "__main__":
    import json
    print("Current Configuration:")
    print(json.dumps(get_config_summary(), indent=2))
