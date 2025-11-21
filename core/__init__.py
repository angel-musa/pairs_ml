"""
Statistical Arbitrage Research Engine - Core Module

This module provides the foundational components for cointegration-based
pairs trading research, including data loading, statistical tests, signal
generation, backtesting, and performance analytics.

Public API:
-----------
Data Loading:
    - load_price_csv: Load price data from CSV
    - align_pairs: Align two price series by date

Cointegration:
    - engle_granger: Test for cointegration between two series
    - rolling_hedge_ratio: Calculate rolling OLS hedge ratios

Signal Generation:
    - compute_spread: Calculate cointegration spread
    - zscore: Compute rolling z-scores
    - mean_reversion_signals: Generate entry/exit signals

Backtesting:
    - backtest_spread_strategy: Run vectorized backtest
    - BacktestResult: Dataclass for backtest outputs

Performance Metrics:
    - summarize_performance: Calculate Sharpe, drawdown, hit rate, etc.
    - PerformanceSummary: Dataclass for metrics

Example:
--------
    from core import (
        load_price_csv,
        engle_granger,
        compute_spread,
        zscore,
        mean_reversion_signals,
        backtest_spread_strategy,
        summarize_performance
    )
    
    # Load data
    df = load_price_csv('data/prices.csv')
    x, y = df['AAA'], df['BBB']
    
    # Test cointegration
    eg_result = engle_granger(x, y)
    
    # Generate signals and backtest
    spread = compute_spread(y, x, eg_result.hedge_ratio)
    z = zscore(spread, window=60)
    signals = mean_reversion_signals(z, entry_z=2.0, exit_z=0.5)
    results = backtest_spread_strategy(spread, signals)
    metrics = summarize_performance(results.returns)
"""

from .data_loader import load_price_csv, align_pairs
from .coint import engle_granger, rolling_hedge_ratio
from .signal import compute_spread, zscore, mean_reversion_signals
from .backtester import backtest_spread_strategy, BacktestResult
from .metrics import summarize_performance, PerformanceSummary

__all__ = [
    # Data loading
    'load_price_csv',
    'align_pairs',
    # Cointegration
    'engle_granger',
    'rolling_hedge_ratio',
    # Signal generation
    'compute_spread',
    'zscore',
    'mean_reversion_signals',
    # Backtesting
    'backtest_spread_strategy',
    'BacktestResult',
    # Metrics
    'summarize_performance',
    'PerformanceSummary',
]

__version__ = '1.0.0'
