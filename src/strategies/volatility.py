import pandas as pd

from .base import SignalType, Strategy


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands Strategy."""

    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__("Bollinger Bands Strategy")
        self.window = window
        self.num_std = num_std

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        sma = data["Close"].rolling(window=self.window).mean()
        std = data["Close"].rolling(window=self.window).std()

        upper_band = sma + (std * self.num_std)
        lower_band = sma - (std * self.num_std)

        signals = pd.Series(SignalType.HOLD, index=data.index)
        signals[data["Close"] < lower_band] = SignalType.BUY
        signals[data["Close"] > upper_band] = SignalType.SELL

        return signals


class ATRTrailingStopStrategy(Strategy):
    """Average True Range Trailing Stop Strategy."""

    def __init__(self, atr_period: int = 14, atr_multiplier: float = 2.0):
        super().__init__("ATR Trailing Stop Strategy")
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Calculate ATR
        tr = pd.DataFrame(
            {
                "hl": data["High"] - data["Low"],
                "hc": abs(data["High"] - data["Close"].shift(1)),
                "lc": abs(data["Low"] - data["Close"].shift(1)),
            }
        ).max(axis=1)

        atr = tr.rolling(window=self.atr_period).mean()

        # Calculate trailing stops
        is_uptrend = True
        stops = []

        for i in range(len(data)):
            if i == 0:
                stops.append(data["Close"].iloc[i])
                continue

            prev_stop = stops[-1]
            curr_close = data["Close"].iloc[i]
            curr_atr = atr.iloc[i]

            if is_uptrend:
                new_stop = max(prev_stop, curr_close - (self.atr_multiplier * curr_atr))
                if curr_close < prev_stop:
                    is_uptrend = False
            else:
                new_stop = min(prev_stop, curr_close + (self.atr_multiplier * curr_atr))
                if curr_close > prev_stop:
                    is_uptrend = True

            stops.append(new_stop)

        stops = pd.Series(stops, index=data.index)

        signals = pd.Series(SignalType.HOLD, index=data.index)
        signals[data["Close"] > stops] = SignalType.BUY
        signals[data["Close"] < stops] = SignalType.SELL

        return signals
