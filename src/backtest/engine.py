from dataclasses import dataclass
from decimal import Decimal

import pandas as pd

from ..core.asset import Asset
from ..core.metrics import MetricsCalculator, PerformanceMetrics
from ..core.position import Position
from ..data.fetcher import DataFetcher
from ..strategies.base import SignalType, Strategy
from ..utils.journal import JournalWriter
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacktestResult:
    """Class to store the results of a backtest."""

    metrics: PerformanceMetrics
    equity_series: pd.Series


class BacktestEngine:
    """Main backtesting engine."""

    # Return type for backtest results

    def __init__(
        self,
        initial_capital: float = 100000,
        position_size: float = 0.1,  # Changed to 10% of capital
        max_positions: int = 5,
        journal: JournalWriter = None,
    ):
        """Initialize the backtest engine."""
        self.initial_capital = Decimal(str(initial_capital))
        self.current_capital = self.initial_capital
        self.position_size = Decimal(str(position_size))
        self.max_positions = max_positions
        self.positions: list[Position] = []
        self.closed_positions: list[Position] = []
        self.equity_curve = []
        self.journal = journal

    def run(
        self,
        strategy: Strategy,
        asset: Asset,
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        interval: str = "1d",
    ) -> BacktestResult:
        """Run backtest for given strategy and asset."""
        with self.journal:
            try:
                self.journal.section(
                    f"Starting backtest for {asset.symbol}", printable=True
                )
                self.journal.metric(
                    "Initial Capital", float(self.initial_capital), printable=True
                )

                # Reset state
                self.current_capital = self.initial_capital
                self.positions = []
                self.closed_positions = []
                self.equity_curve = []

                # Fetch data
                data_fetcher = DataFetcher()
                data = data_fetcher.get_data(asset, start_date, end_date, interval)

                self.journal.write(f"Fetched {len(data)} bars of data", printable=True)
                self.journal.write(
                    f"Initial capital: ${self.initial_capital}", printable=True
                )
                self.journal.write(
                    f"Sample prices: {data['Close'].head().tolist()}", printable=True
                )

                # Generate signals
                signals = strategy.generate_signals(data)

                # Process each bar
                for i in range(len(data)):
                    current_bar = data.iloc[i]
                    current_time = data.index[i]
                    current_signal = signals.iloc[i]

                    # Process signals before updating positions
                    if current_signal == SignalType.BUY:
                        self.journal.write(f"\nProcessing BUY signal at {current_time}")
                        self.journal.write(f"Current price: {current_bar['Close']}")
                        self.journal.write(f"Current capital: {self.current_capital}")
                        self._open_position(asset, current_bar, current_time)
                    elif current_signal == SignalType.SELL and len(self.positions) > 0:
                        self.journal.write(
                            f"\nProcessing SELL signal at {current_time}"
                        )
                        self.journal.write(f"Current price: {current_bar['Close']}")
                        self.journal.write(f"Current capital: {self.current_capital}")
                        self._close_positions(asset, current_bar, current_time)

                    # Update open positions
                    self._update_positions(current_bar, current_time)

                    # Record equity
                    current_equity = self._calculate_equity(current_bar)
                    self.equity_curve.append(float(current_equity))

                    if i % 100 == 0 or len(self.positions) > 0:
                        self.journal.write(
                            f"Bar {i}: Equity=${current_equity}, Open Positions={len(self.positions)}"
                        )

                # Close any remaining positions
                self._close_all_positions(data.iloc[-1], data.index[-1])

                # Calculate performance metrics
                equity_series = pd.Series(self.equity_curve, index=data.index)

                equity_series = pd.Series(self.equity_curve, index=data.index)
                metrics = MetricsCalculator.calculate_metrics(
                    self.closed_positions, equity_series
                )

                return BacktestResult(metrics=metrics, equity_series=equity_series)

            except Exception as e:
                logger.error(f"Backtest failed: {str(e)}")
                import traceback

                traceback.print_exc()
                raise

    # Example modification for portfolio backtesting
    def run_portfolio(
        self,
        strategies: dict[str, Strategy],
        assets: list[Asset],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
        interval: str = "1d",
    ) -> PerformanceMetrics:
        """Run backtest for a portfolio of assets."""
        try:
            self.journal.section(
                f"Starting portfolio backtest with {len(assets)} assets", printable=True
            )

            # Reset state
            self.current_capital = self.initial_capital
            self.positions = []
            self.closed_positions = []
            self.equity_curve = []

            # Fetch and prepare data
            data_fetcher = DataFetcher()
            portfolio_data = {}
            all_dates = set()

            for asset in assets:
                data = data_fetcher.get_data(asset, start_date, end_date, interval)
                portfolio_data[asset.symbol] = data
                all_dates.update(data.index)
                self.journal.write(
                    f"Fetched {len(data)} bars for {asset.symbol}", printable=True
                )
                self.journal.write(
                    f"Date range: {data.index[0]} to {data.index[-1]}", printable=True
                )

            dates = sorted(all_dates)
            trading_days_elapsed = 0
            last_log_date = None

            # Generate signals
            self.journal.section("Generating signals", printable=True)
            portfolio_signals = {}
            for asset in assets:
                strategy = strategies[asset.symbol]
                signals = strategy.generate_signals(portfolio_data[asset.symbol])
                portfolio_signals[asset.symbol] = signals
                self.journal.write(
                    f"Generated signals for {asset.symbol} using {strategy.name}",
                    printable=True,
                )

            # Initialize equity curve with initial capital
            equity_values = []
            equity_dates = []
            equity_values.append(float(self.initial_capital))
            equity_dates.append(dates[0])

            # Process each date
            previous_date = None
            for current_time in dates:
                # Check if this is a new trading day
                if previous_date is None or current_time.date() != previous_date.date():
                    trading_days_elapsed += 1
                    previous_date = current_time

                # Process signals for each asset
                current_bars = {}
                for asset in assets:
                    data = portfolio_data[asset.symbol]
                    if current_time not in data.index:
                        continue

                    current_bar = data.loc[current_time]
                    current_bars[asset.symbol] = current_bar
                    current_signal = portfolio_signals[asset.symbol].loc[current_time]

                    if current_signal == SignalType.BUY:
                        self.journal.write(
                            f"\nProcessing BUY signal for {asset.symbol} at {current_time}"
                        )
                        self._open_position(asset, current_bar, current_time)
                    elif current_signal == SignalType.SELL:
                        self.journal.write(
                            f"\nProcessing SELL signal for {asset.symbol} at {current_time}"
                        )
                        self._close_positions(asset, current_bar, current_time)

                # Update positions
                for asset in assets:
                    if current_time in portfolio_data[asset.symbol].index:
                        current_bar = portfolio_data[asset.symbol].loc[current_time]
                        self._update_positions(current_bar, current_time)

                # Calculate total portfolio value (cash + positions)
                total_value = float(self.current_capital)
                for position in self.positions:
                    if position.symbol in current_bars:
                        current_price = float(current_bars[position.symbol]["Close"])
                        position_value = float(position.shares) * current_price
                        total_value += position_value

                equity_values.append(total_value)
                equity_dates.append(current_time)

                # Check if it's a new day before making logging decision
                if current_time.date() != last_log_date:
                    self.journal.write(
                        f"\nTrading Day {trading_days_elapsed} ({current_time.date()}): "
                        f"Portfolio Equity=${total_value:,.2f}, "
                        f"Open Positions={len(self.positions)}"
                    )
                    last_log_date = current_time.date()

            # Close remaining positions
            self.journal.write("\nClosing remaining positions...")
            for asset in assets:
                data = portfolio_data[asset.symbol]
                final_bar = data.iloc[-1]
                self._close_positions(asset, final_bar, data.index[-1])

            # Create final equity curve
            equity_series = pd.Series(equity_values, index=equity_dates)

            # Print final results
            self.journal.section("Final Results", printable=False)
            self.journal.metric(
                "Starting Capital", float(self.initial_capital), printable=False
            )
            self.journal.metric(
                "Final Capital", float(self.current_capital), printable=False
            )
            self.journal.metric(
                "Total Trades", len(self.closed_positions), printable=False
            )

            if self.closed_positions:
                total_pnl = sum(pos.profit_loss for pos in self.closed_positions)
                self.journal.metric("Total P&L", float(total_pnl), printable=False)
                self.journal.metric(
                    "Average P&L per trade",
                    float(total_pnl / len(self.closed_positions)),
                    printable=False,
                )

            equity_series = pd.Series(equity_values, index=equity_dates)
            metrics = MetricsCalculator.calculate_metrics(
                self.closed_positions, equity_series
            )

            return BacktestResult(metrics=metrics, equity_series=equity_series)

        except Exception as e:
            logger.error(f"Portfolio backtest failed: {str(e)}")
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
            # Only check max positions limit
            if len(self.positions) >= self.max_positions:
                self.journal.write(
                    f"Skip opening position: Max positions ({self.max_positions}) reached"
                )
                return

            # Calculate position size
            position_capital = self.current_capital * self.position_size
            current_price = Decimal(str(bar["Close"]))

            if current_price == 0:
                self.journal.write(
                    f"Skip opening position: Invalid price {current_price}"
                )
                return

            shares = float(position_capital / current_price)
            shares = round(shares, 3)
            shares_decimal = Decimal(str(shares))

            if shares < 0.001:
                self.journal.write(
                    "Skip opening position: Position size too small", printable=True
                )
                return

            position = Position(
                symbol=asset.symbol,
                entry_price=current_price,
                entry_date=timestamp,
                shares=shares_decimal,
            )

            cost = current_price * shares_decimal
            if cost > self.current_capital:
                self.journal.write("Skip opening position: Insufficient capital")
                return

            self.journal.write(f"\nOpening position #{len(self.positions) + 1}:")
            self.journal.write(f"Symbol: {position.symbol}")
            self.journal.write(f"Shares: {float(shares_decimal):,.3f}")
            self.journal.write(f"Price: ${float(current_price):,.2f}")
            self.journal.write(f"Total Cost: ${float(cost):,.2f}")
            self.journal.write(f"Capital Before: ${float(self.current_capital):,.2f}")

            self.positions.append(position)
            self.current_capital -= cost

            self.journal.write(f"Total Open Positions: {len(self.positions)}")

        except Exception as e:
            self.journal.write(f"Error opening position: {str(e)}", printable=True)

    def _close_position(
        self, position: Position, price: Decimal, timestamp: pd.Timestamp
    ):
        """Close specific position."""
        try:
            if not position.is_open:
                return

            position.exit_price = price
            position.exit_date = timestamp

            value = price * Decimal(str(position.shares))
            pnl = position.profit_loss

            self.journal.write("\nClosing position:")
            self.journal.write(f"Symbol: {position.symbol}")
            self.journal.write(f"Shares: {position.shares:,}")
            self.journal.write(f"Entry: ${float(position.entry_price):,.2f}")
            self.journal.write(f"Exit: ${float(price):,.2f}")
            self.journal.write(f"P&L: ${float(pnl):,.2f}")
            self.journal.write(f"Capital Before: ${float(self.current_capital):,.2f}")

            self.current_capital += value
            self.closed_positions.append(position)
            self.positions.remove(position)

            self.journal.write(f"Capital After: ${float(self.current_capital):,.2f}")

        except Exception as e:
            self.journal.write(f"Error closing position: {str(e)}", printable=True)
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
            Decimal(str(position.shares))
            * Decimal(str(bar["Close"]))  # Convert both to Decimal
            for position in self.positions
        )
        return self.current_capital + open_positions_value

    def _calculate_portfolio_equity(
        self, current_bars: dict[str, pd.Series]
    ) -> Decimal:
        """Calculate current equity including all portfolio positions."""
        try:
            # Start with current cash
            total_equity = self.current_capital

            # Add value of all open positions
            for position in self.positions:
                if position.symbol in current_bars:
                    current_bar = current_bars[position.symbol]
                    position_value = position.shares * Decimal(
                        str(current_bar["Close"])
                    )
                    total_equity += position_value

            return total_equity

        except Exception as e:
            logger.error(f"Error calculating portfolio equity: {str(e)}")
            return self.current_capital
