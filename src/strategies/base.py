from abc import ABC, abstractmethod
from typing import List, Optional
import pandas as pd
import numpy as np


class SignalType:
    BUY = 1
    SELL = -1
    HOLD = 0


class Strategy(ABC):
    """Base class for trading strategies"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals"""
        pass

    def calculate_position_size(self, capital: float, price: float) -> int:
        """Calculate position size based on available capital"""
        return int(capital * 0.02 / price)  # 2% risk per trade
