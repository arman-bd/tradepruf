"""Example script demonstrating how to use TradePruf for a simple backtest."""
import pandas as pd

from src.backtest.engine import BacktestEngine
from src.core.asset import Asset, AssetType
from src.strategies.moving_average import SMACrossoverStrategy


def main():
    # Initialize components
    asset = Asset("AAPL", AssetType.STOCK)
    strategy = SMACrossoverStrategy(short_window=20, long_window=50)
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
    print(f"\nBacktest Results for {asset.symbol}:")
    print(f"Total Return: {metrics.total_return:.2f}%")
    print(f"Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {metrics.max_drawdown:.2f}%")
    print(f"Win Rate: {metrics.win_rate * 100:.2f}%")


if __name__ == "__main__":
    main()
