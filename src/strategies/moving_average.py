import pandas as pd

from ..utils.journal import JournalWriter
from .base import SignalType, Strategy


class SMACrossoverStrategy(Strategy):
    """Simple Moving Average Crossover Strategy."""

    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 50,
        journal: JournalWriter = None,
    ):
        super().__init__("SMA Crossover")
        self.short_window = short_window
        self.long_window = long_window
        self.journal = journal

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if len(data) < self.long_window:
            return pd.Series(SignalType.HOLD, index=data.index)

        # Calculate moving averages
        short_ma = data["Close"].rolling(window=self.short_window, min_periods=1).mean()
        long_ma = data["Close"].rolling(window=self.long_window, min_periods=1).mean()

        # Initialize signals
        signals = pd.Series(SignalType.HOLD, index=data.index)

        # Previous position tracker (0: out of market, 1: in market)
        position = 0

        # Generate crossover signals only on actual crossovers
        for i in range(self.long_window, len(data)):
            if short_ma.iloc[i] > long_ma.iloc[i] and position == 0:
                signals.iloc[i] = SignalType.BUY
                position = 1
            elif short_ma.iloc[i] < long_ma.iloc[i] and position == 1:
                signals.iloc[i] = SignalType.SELL
                position = 0

        self.journal.write(
            f"Generated SMA Crossover signals: Buy={sum(signals == SignalType.BUY)}, Sell={sum(signals == SignalType.SELL)}",
            printable=True,
        )

        return signals


class EMAStrategy(Strategy):
    """Exponential Moving Average Strategy."""

    def __init__(
        self,
        fast_window: int = 12,
        slow_window: int = 26,
        journal: JournalWriter = None,
    ):
        super().__init__("EMA Strategy")
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.journal = journal

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        fast_ema = data["Close"].ewm(span=self.fast_window, adjust=False).mean()
        slow_ema = data["Close"].ewm(span=self.slow_window, adjust=False).mean()

        signals = pd.Series(SignalType.HOLD, index=data.index)
        signals[fast_ema > slow_ema] = SignalType.BUY
        signals[fast_ema < slow_ema] = SignalType.SELL

        self.journal.write(
            f"Generated EMA signals: Buy={sum(signals == SignalType.BUY)}, Sell={sum(signals == SignalType.SELL)}",
            printable=True,
        )

        return signals
