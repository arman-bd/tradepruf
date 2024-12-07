"""TradePruf: A flexible framework for backtesting trading strategies.

This package provides tools for:
- Backtesting trading strategies
- Processing market data
- Analyzing trading performance
- Visualizing results
"""

__version__ = "0.1.0"

from .backtest.engine import BacktestEngine
from .core.asset import Asset, AssetType
from .core.metrics import PerformanceMetrics
from .core.position import Position
from .data.fetcher import DataFetcher
from .strategies.base import SignalType, Strategy
from .strategies.momentum import (
    MACDStrategy,
    RSIStrategy,
)
from .strategies.moving_average import (
    EMAStrategy,
    SMACrossoverStrategy,
)
from .strategies.volatility import (
    ATRTrailingStopStrategy,
    BollingerBandsStrategy,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "Asset",
    "AssetType",
    "Position",
    "PerformanceMetrics",
    # Engine
    "BacktestEngine",
    # Strategy base
    "Strategy",
    "SignalType",
    # Strategy implementations
    "SMACrossoverStrategy",
    "EMAStrategy",
    "RSIStrategy",
    "MACDStrategy",
    "BollingerBandsStrategy",
    "ATRTrailingStopStrategy",
    # Data
    "DataFetcher",
]
