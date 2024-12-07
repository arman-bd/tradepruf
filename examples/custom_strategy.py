"""Example script showing how to create and use a custom strategy."""
import pandas as pd

from src.backtest.engine import BacktestEngine
from src.core.asset import Asset, AssetType
from src.strategies.base import SignalType, Strategy


class CustomStrategy(Strategy):
    """Custom strategy combining RSI and Bollinger Bands."""

    def __init__(self, rsi_period: int = 14, bb_period: int = 20):
        super().__init__("Custom RSI+BB Strategy")
        self.rsi_period = rsi_period
        self.bb_period = bb_period

    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        # Calculate RSI
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # Calculate Bollinger Bands
        sma = data["Close"].rolling(window=self.bb_period).mean()
        std = data["Close"].rolling(window=self.bb_period).std()
        lower_band = sma - (2 * std)

        # Generate signals
        signals = pd.Series(SignalType.HOLD, index=data.index)

        # Buy when RSI < 30 and price below lower band
        buy_condition = (rsi < 30) & (data["Close"] < lower_band)
        signals[buy_condition] = SignalType.BUY

        # Sell when RSI > 70
        signals[rsi > 70] = SignalType.SELL

        return signals


def main():
    # Initialize components
    asset = Asset("MSFT", AssetType.STOCK)
    strategy = CustomStrategy(rsi_period=14, bb_period=20)
    engine = BacktestEngine(initial_capital=100000)

    # Run backtest
    metrics = engine.run(
        strategy=strategy,
        asset=asset,
        start_date=pd.Timestamp("2023-01-01"),
        end_date=pd.Timestamp("2023-12-31"),
        interval="1d",
    )

    # Print results
    print(f"\nBacktest Results for Custom Strategy on {asset.symbol}:")
    print(f"Total Return: {metrics.total_return:.2f}%")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Win Rate: {metrics.win_rate * 100:.2f}%")


if __name__ == "__main__":
    main()
