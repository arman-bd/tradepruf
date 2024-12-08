import pandas as pd
import numpy as np
from .base import Strategy, SignalType


class RSIStrategy(Strategy):
    """Relative Strength Index Strategy."""

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI Strategy")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if len(data) < self.period:
            return pd.Series(SignalType.HOLD, index=data.index)

        # Previous position tracker
        position = 0
        signals = pd.Series(SignalType.HOLD, index=data.index)

        # Calculate RSI
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        print(f"Generated RSI values: Min={rsi.min():.2f}, Max={rsi.max():.2f}")

        # Generate signals only on crossovers
        for i in range(self.period, len(data)):
            if rsi.iloc[i] < self.oversold and position == 0:
                signals.iloc[i] = SignalType.BUY
                position = 1
            elif rsi.iloc[i] > self.overbought and position == 1:
                signals.iloc[i] = SignalType.SELL
                position = 0

        print(
            f"Generated RSI signals: Buy={sum(signals == SignalType.BUY)}, "
            f"Sell={sum(signals == SignalType.SELL)}"
        )
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
        if len(data) < self.slow_period + self.signal_period:
            return pd.Series(SignalType.HOLD, index=data.index)

        # Previous position tracker
        position = 0
        signals = pd.Series(SignalType.HOLD, index=data.index)

        # Calculate MACD
        fast_ema = data["Close"].ewm(span=self.fast_period, adjust=False).mean()
        slow_ema = data["Close"].ewm(span=self.slow_period, adjust=False).mean()
        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()

        # Generate signals only on crossovers
        for i in range(self.slow_period + self.signal_period, len(data)):
            if macd_line.iloc[i] > signal_line.iloc[i] and position == 0:
                signals.iloc[i] = SignalType.BUY
                position = 1
            elif macd_line.iloc[i] < signal_line.iloc[i] and position == 1:
                signals.iloc[i] = SignalType.SELL
                position = 0

        print(
            f"Generated MACD signals: Buy={sum(signals == SignalType.BUY)}, "
            f"Sell={sum(signals == SignalType.SELL)}"
        )
        return signals
