from decimal import Decimal

import pandas as pd

from ..core.asset import Asset
from ..core.metrics import MetricsCalculator, PerformanceMetrics
from ..core.position import Position
from ..data.fetcher import DataFetcher
from ..strategies.base import SignalType, Strategy
from ..utils.logger import get_logger

logger = get_logger(__name__)


class BacktestEngine:
    """Main backtesting engine."""

    def __init__(
        self,
        initial_capital: float = 100000,
        position_size: float = 0.2,  # Changed to 20% of capital
        max_positions: int = 5,
    ):
        self.initial_capital = Decimal(str(initial_capital))
        self.current_capital = self.initial_capital
        self.position_size = Decimal(str(position_size))
        self.max_positions = max_positions
        self.positions: list[Position] = []
        self.closed_positions: list[Position] = []
        self.equity_curve = []

    def run(self, strategy: Strategy, asset: Asset, start_date: pd.Timestamp, 
            end_date: pd.Timestamp, interval: str = "1d") -> PerformanceMetrics:
        """Run backtest for given strategy and asset."""
        try:
            logger.info(f"Starting backtest for {asset.symbol} using {strategy.name}")
            
            # Reset state
            self.current_capital = self.initial_capital
            self.positions = []
            self.closed_positions = []
            self.equity_curve = []

            # Fetch data
            data_fetcher = DataFetcher()
            data = data_fetcher.get_data(asset, start_date, end_date, interval)
            
            print(f"Fetched {len(data)} bars of data")
            print(f"Initial capital: ${self.initial_capital}")
            print(f"Sample prices: {data['Close'].head().tolist()}")

            # Generate signals
            signals = strategy.generate_signals(data)
            
            # Process each bar
            for i in range(len(data)):
                current_bar = data.iloc[i]
                current_time = data.index[i]
                current_signal = signals.iloc[i]

                # Process signals before updating positions
                if current_signal == SignalType.BUY:
                    print(f"\nProcessing BUY signal at {current_time}")
                    print(f"Current price: {current_bar['Close']}")
                    print(f"Current capital: {self.current_capital}")
                    self._open_position(asset, current_bar, current_time)
                elif current_signal == SignalType.SELL and len(self.positions) > 0:
                    print(f"\nProcessing SELL signal at {current_time}")
                    self._close_positions(asset, current_bar, current_time)

                # Update open positions
                self._update_positions(current_bar, current_time)

                # Record equity
                current_equity = self._calculate_equity(current_bar)
                self.equity_curve.append(float(current_equity))

                if i % 100 == 0 or len(self.positions) > 0:
                    print(f"Bar {i}: Equity=${current_equity}, Open Positions={len(self.positions)}")

            # Close any remaining positions
            self._close_all_positions(data.iloc[-1], data.index[-1])

            # Calculate performance metrics
            equity_series = pd.Series(self.equity_curve, index=data.index)
            
            print(f"\nFinal Results:")
            print(f"Starting Capital: ${self.initial_capital}")
            print(f"Final Capital: ${self.current_capital}")
            print(f"Total Trades: {len(self.closed_positions)}")
            
            if len(self.closed_positions) > 0:
                total_pnl = sum(pos.profit_loss for pos in self.closed_positions)
                print(f"Total P&L: ${total_pnl}")
                print(f"Average P&L per trade: ${total_pnl / len(self.closed_positions)}")
            
            metrics = MetricsCalculator.calculate_metrics(
                self.closed_positions, equity_series
            )

            return metrics

        except Exception as e:
            logger.error(f"Backtest failed: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def _update_positions(self, bar: pd.Series, timestamp: pd.Timestamp):
        """Update open positions with current prices."""
        for position in self.positions:
            # Check stop loss
            if position.stop_loss and bar["Low"] <= position.stop_loss:
                self._close_position(position, position.stop_loss, timestamp)
                continue

            # Check take profit
            if position.take_profit and bar["High"] >= position.take_profit:
                self._close_position(position, position.take_profit, timestamp)
                continue

    def _open_position(self, asset: Asset, bar: pd.Series, timestamp: pd.Timestamp):
        """Open new position if conditions are met."""
        try:
            if any(p.symbol == asset.symbol for p in self.positions):
                print(f"Skip opening position: Already have position in {asset.symbol}")
                return

            if len(self.positions) >= self.max_positions:
                print(f"Skip opening position: Max positions ({self.max_positions}) reached")
                return

            # Calculate position size (20% of current capital)
            position_capital = self.current_capital * self.position_size
            current_price = Decimal(str(bar["Close"]))
            
            if current_price == 0:
                print(f"Skip opening position: Invalid price {current_price}")
                return
                
            # Calculate shares and convert to Decimal for consistent handling
            shares = float(position_capital / current_price)
            shares = round(shares, 3)  # Round to 3 decimal places
            shares_decimal = Decimal(str(shares))
            
            if shares < 0.001:
                print(f"Skip opening position: Position size too small (capital: {position_capital}, price: {current_price})")
                return

            # Create position with Decimal shares
            position = Position(
                symbol=asset.symbol,
                entry_price=current_price,
                entry_date=timestamp,
                shares=shares_decimal,  # Store as Decimal
            )

            cost = current_price * shares_decimal
            if cost > self.current_capital:
                print(f"Skip opening position: Insufficient capital (need: {cost}, have: {self.current_capital})")
                return

            print(f"\nOpening position:")
            print(f"Symbol: {position.symbol}")
            print(f"Shares: {float(shares_decimal):,.3f}")
            print(f"Price: ${float(current_price):,.2f}")
            print(f"Total Cost: ${float(cost):,.2f}")
            print(f"Capital Before: ${float(self.current_capital):,.2f}")
            
            self.positions.append(position)
            self.current_capital -= cost
            
            print(f"Capital After: ${float(self.current_capital):,.2f}")

        except Exception as e:
            print(f"Error opening position: {str(e)}")
            import traceback
            traceback.print_exc()

    def _close_position(self, position: Position, price: Decimal, timestamp: pd.Timestamp):
        """Close specific position."""
        try:
            if not position.is_open:
                return

            position.exit_price = price
            position.exit_date = timestamp

            value = price * Decimal(str(position.shares))
            pnl = position.profit_loss

            print(f"\nClosing position:")
            print(f"Symbol: {position.symbol}")
            print(f"Shares: {position.shares:,}")
            print(f"Entry: ${float(position.entry_price):,.2f}")
            print(f"Exit: ${float(price):,.2f}")
            print(f"P&L: ${float(pnl):,.2f}")
            print(f"Capital Before: ${float(self.current_capital):,.2f}")

            self.current_capital += value
            self.closed_positions.append(position)
            self.positions.remove(position)

            print(f"Capital After: ${float(self.current_capital):,.2f}")

        except Exception as e:
            print(f"Error closing position: {str(e)}")
            import traceback
            traceback.print_exc()

    def _close_positions(self, asset: Asset, bar: pd.Series, timestamp: pd.Timestamp):
        """Close all positions for given asset."""
        positions_to_close = [p for p in self.positions if p.symbol == asset.symbol]
        for position in positions_to_close:
            self._close_position(position, Decimal(str(bar["Close"])), timestamp)

    def _close_all_positions(self, bar: pd.Series, timestamp: pd.Timestamp):
        """Close all open positions."""
        while self.positions:
            position = self.positions[0]
            self._close_position(position, Decimal(str(bar["Close"])), timestamp)

    def _calculate_equity(self, bar: pd.Series) -> Decimal:
        """Calculate current equity including open positions."""
        open_positions_value = sum(
            Decimal(str(position.shares)) * Decimal(str(bar["Close"]))  # Convert both to Decimal
            for position in self.positions
        )
        return self.current_capital + open_positions_value
