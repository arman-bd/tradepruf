from abc import ABC, abstractmethod

import pandas as pd

from ..utils.journal import JournalWriter


class SignalType:
    BUY = 1
    SELL = -1
    HOLD = 0


class Strategy(ABC):
    """Base class for trading strategies."""

    def __init__(self, name: str, journal: JournalWriter = None):
        self.name = name
        self.journal = journal

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals."""
        pass

    def calculate_position_size(self, capital: float, price: float) -> int:
        """Calculate position size based on available capital."""
        return int(capital * 0.02 / price)  # 2% risk per trade
