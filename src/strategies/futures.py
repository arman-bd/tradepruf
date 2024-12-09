import pandas as pd

from ..utils.journal import JournalWriter
from .base import SignalType, Strategy


class FuturesStrategy(Strategy):
    """Futures trading strategy with dynamic leverage management."""

    def __init__(
        self,
        volatility_window: int = 20,
        atr_periods: int = 14,
        atr_multiplier: float = 2.0,
        rsi_period: int = 14,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        trend_short_window: int = 10,
        trend_long_window: int = 50,
        max_leverage: float = 5.0,
        min_leverage: float = 1.0,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        profit_ratio: float = 2.0,     # Risk:Reward ratio
        journal: JournalWriter = None,
    ):
        """Initialize strategy parameters."""
        super().__init__("Futures Strategy", journal)
        self.volatility_window = volatility_window
        self.atr_periods = atr_periods
        self.atr_multiplier = atr_multiplier
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.trend_short_window = trend_short_window
        self.trend_long_window = trend_long_window
        self.max_leverage = float(max_leverage)  # Ensure float conversion
        self.min_leverage = float(min_leverage)
        self.risk_per_trade = risk_per_trade
        self.profit_ratio = profit_ratio
        
        # Store calculated values for position management
        self.current_leverage = float(max_leverage)  # Start with max leverage
        self.current_stop_loss = None
        self.current_take_profit = None

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """Generate trading signals with dynamic leverage and risk management."""
        if len(data) < max(self.volatility_window, self.atr_periods, self.rsi_period):
            return pd.Series(SignalType.HOLD, index=data.index)

        # Calculate technical indicators
        atr = self._calculate_atr(data)
        volatility = self._calculate_volatility(data)
        rsi = self._calculate_rsi(data)
        trend = self._calculate_trend(data)
        
        # Initialize signals and tracking variables
        signals = pd.Series(SignalType.HOLD, index=data.index)
        position_open = False
        
        for i in range(max(self.volatility_window, self.atr_periods, self.rsi_period), len(data)):
            current_price = data['Close'].iloc[i]
            current_atr = atr.iloc[i]
            current_vol = volatility.iloc[i]
            
            if not position_open:
                # Entry conditions
                long_signal = (
                    rsi.iloc[i] < self.rsi_oversold and
                    trend.iloc[i] > 0 and
                    current_vol < volatility.rolling(window=20).mean().iloc[i]
                )
                
                short_signal = (
                    rsi.iloc[i] > self.rsi_overbought and
                    trend.iloc[i] < 0 and
                    current_vol < volatility.rolling(window=20).mean().iloc[i]
                )
                
                if long_signal or short_signal:
                    # Always use maximum leverage for futures
                    self.current_leverage = self.max_leverage
                    
                    # Calculate stop loss and take profit levels
                    stop_distance = current_atr * self.atr_multiplier
                    if long_signal:
                        self.current_stop_loss = current_price - stop_distance
                        self.current_take_profit = current_price + (stop_distance * self.profit_ratio)
                    else:  # short signal
                        self.current_stop_loss = current_price + stop_distance
                        self.current_take_profit = current_price - (stop_distance * self.profit_ratio)
                    
                    signals.iloc[i] = SignalType.BUY
                    position_open = True
            
            elif position_open:
                # Exit conditions
                exit_signal = (
                    (current_price <= self.current_stop_loss) or
                    (current_price >= self.current_take_profit) or
                    (rsi.iloc[i] > self.rsi_overbought and trend.iloc[i] < 0) or
                    (rsi.iloc[i] < self.rsi_oversold and trend.iloc[i] > 0)
                )
                
                if exit_signal:
                    signals.iloc[i] = SignalType.SELL
                    position_open = False

        self.journal.write(
            f"Generated Futures signals: Buy={sum(signals == SignalType.BUY)}, Sell={sum(signals == SignalType.SELL)}",
            printable=True,
        )

        return signals

    def _calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        high = data["High"]
        low = data["Low"]
        close = data["Close"].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=self.atr_periods).mean()

    def _calculate_volatility(self, data: pd.DataFrame) -> pd.Series:
        """Calculate rolling volatility."""
        returns = data["Close"].pct_change()
        return returns.rolling(window=self.volatility_window).std()

    def _calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()

        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def _calculate_trend(self, data: pd.DataFrame) -> pd.Series:
        """Calculate trend strength using EMA difference."""
        short_ema = data["Close"].ewm(span=self.trend_short_window, adjust=False).mean()
        long_ema = data["Close"].ewm(span=self.trend_long_window, adjust=False).mean()

        # Normalize trend strength between -1 and 1
        trend = (short_ema - long_ema) / long_ema
        return trend

    def _calculate_dynamic_leverage(
        self, current_volatility: float, trend_strength: float, avg_volatility: float
    ) -> float:
        """Calculate appropriate leverage based on market conditions."""
        # Reduce leverage when volatility is high
        vol_ratio = min(
            avg_volatility / current_volatility if current_volatility > 0 else 1, 2
        )
        base_leverage = vol_ratio * self.max_leverage

        # Adjust leverage based on trend strength
        trend_factor = min(abs(trend_strength) * 2, 1)  # Scale trend strength
        leverage = base_leverage * trend_factor

        # Ensure leverage stays within bounds
        leverage = max(min(leverage, self.max_leverage), self.min_leverage)

        return round(leverage, 2)

    def get_suggested_position_size(self, capital: float, price: float) -> float:
        """Calculate suggested position size based on risk parameters."""
        risk_amount = capital * self.risk_per_trade
        position_value = risk_amount * self.current_leverage
        return position_value / price

    def get_current_leverage(self) -> float:
        """Get the currently calculated leverage for the next trade."""
        return self.current_leverage

    def get_stop_loss(self) -> float | None:
        """Get the calculated stop loss for the current/next trade."""
        return self.current_stop_loss

    def get_take_profit(self) -> float | None:
        """Get the calculated take profit for the current/next trade."""
        return self.current_take_profit
