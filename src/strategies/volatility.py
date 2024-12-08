import pandas as pd

from ..utils.journal import JournalWriter
from .base import SignalType, Strategy


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands Strategy."""

    def __init__(
        self, window: int = 20, num_std: float = 2.0, journal: JournalWriter = None
    ):
        super().__init__("Bollinger Bands Strategy")
        self.window = window
        self.num_std = num_std
        self.journal = journal

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if len(data) < self.window:
            return pd.Series(SignalType.HOLD, index=data.index)

        position = 0
        signals = pd.Series(SignalType.HOLD, index=data.index)

        # Calculate Bollinger Bands
        sma = data["Close"].rolling(window=self.window).mean()
        std = data["Close"].rolling(window=self.window).std()
        upper_band = sma + (std * self.num_std)
        lower_band = sma - (std * self.num_std)

        # Generate signals only on band crosses
        for i in range(self.window, len(data)):
            if data["Close"].iloc[i] < lower_band.iloc[i] and position == 0:
                signals.iloc[i] = SignalType.BUY
                position = 1
            elif data["Close"].iloc[i] > upper_band.iloc[i] and position == 1:
                signals.iloc[i] = SignalType.SELL
                position = 0

        self.journal.write(
            f"Generated Bollinger Bands signals: Buy={sum(signals == SignalType.BUY)}, Sell={sum(signals == SignalType.SELL)}",
            printable=True,
        )
        return signals


class ATRTrailingStopStrategy(Strategy):
    """Average True Range Trailing Stop Strategy."""

    def __init__(
        self,
        atr_period: int = 14,
        atr_multiplier: float = 2.0,
        journal: JournalWriter = None,
    ):
        super().__init__("ATR Trailing Stop Strategy")
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
        self.journal = journal

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        if len(data) < self.atr_period:
            return pd.Series(SignalType.HOLD, index=data.index)

        position = 0
        signals = pd.Series(SignalType.HOLD, index=data.index)

        # Calculate ATR
        tr = pd.DataFrame(
            {
                "hl": data["High"] - data["Low"],
                "hc": abs(data["High"] - data["Close"].shift(1)),
                "lc": abs(data["Low"] - data["Close"].shift(1)),
            }
        ).max(axis=1)

        atr = tr.rolling(window=self.atr_period).mean()
        stops = data["Close"].copy()

        # Calculate trailing stops and signals
        for i in range(1, len(data)):
            prev_stop = stops.iloc[i - 1]
            curr_close = data["Close"].iloc[i]
            curr_atr = atr.iloc[i]

            # Update stop
            if position == 1:  # In long position
                stops.iloc[i] = max(
                    prev_stop, curr_close - (self.atr_multiplier * curr_atr)
                )
            else:  # Not in position
                stops.iloc[i] = curr_close - (self.atr_multiplier * curr_atr)

            # Generate signals
            if curr_close > stops.iloc[i] and position == 0:
                signals.iloc[i] = SignalType.BUY
                position = 1
            elif curr_close < stops.iloc[i] and position == 1:
                signals.iloc[i] = SignalType.SELL
                position = 0

        self.journal.write(
            f"Generated ATR signals: Buy={sum(signals == SignalType.BUY)}, Sell={sum(signals == SignalType.SELL)}",
            printable=True,
        )
        return signals
