from enum import Enum

import pandas as pd

from .base import Strategy


class SignalType(Enum):
    HOLD = 0
    BUY = 1
    SELL = 2


class RSIStrategy(Strategy):
    """Relative Strength Index Strategy."""

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Strategy")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(SignalType.HOLD, index=data.index)
        signals[rsi < self.oversold] = SignalType.BUY
        signals[rsi > self.overbought] = SignalType.SELL

        return signals


class MACDStrategy(Strategy):
    """Moving Average Convergence Divergence Strategy."""

    def __init__(
        self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9
    ):
        super().__init__("MACD Strategy")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Calculate MACD line
        fast_ema = data["Close"].ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = data["Close"].ewm(span=self.slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema

        # Calculate signal line
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        signals = pd.Series(SignalType.HOLD, index=data.index)
        signals[macd_line > signal_line] = SignalType.BUY
        signals[macd_line < signal_line] = SignalType.SELL

        return signals
