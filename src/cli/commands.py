import click
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..backtest.engine import BacktestEngine
from ..core.asset import Asset, AssetType
from ..strategies.momentum import MACDStrategy, RSIStrategy
from ..strategies.moving_average import EMAStrategy, SMACrossoverStrategy
from ..strategies.volatility import ATRTrailingStopStrategy, BollingerBandsStrategy

console = Console()

STRATEGIES = {
    "sma": lambda params: SMACrossoverStrategy(
        short_window=int(params.get("short_window", 20)),
        long_window=int(params.get("long_window", 50)),
    ),
    "ema": lambda params: EMAStrategy(
        fast_window=int(params.get("fast_window", 12)),
        slow_window=int(params.get("slow_window", 26)),
    ),
    "rsi": lambda params: RSIStrategy(
        period=int(params.get("period", 14)),
        oversold=int(params.get("oversold", 30)),
        overbought=int(params.get("overbought", 70)),
    ),
    "macd": lambda params: MACDStrategy(
        fast_period=int(params.get("fast_period", 12)),
        slow_period=int(params.get("slow_period", 26)),
        signal_period=int(params.get("signal_period", 9)),
    ),
    "bb": lambda params: BollingerBandsStrategy(
        window=int(params.get("window", 20)), num_std=float(params.get("num_std", 2.0))
    ),
    "atr": lambda params: ATRTrailingStopStrategy(
        atr_period=int(params.get("atr_period", 14)),
        atr_multiplier=float(params.get("atr_multiplier", 2.0)),
    ),
}


@click.group()
def cli():
    """TradePruf - Advanced Trading Strategy Backtester."""
    pass


@cli.command()
@click.option("--symbol", prompt="Enter symbol", help="Asset symbol to trade")
@click.option(
    "--asset-type",
    type=click.Choice([t.value for t in AssetType]),
    prompt="Choose asset type",
    help="Type of asset",
)
@click.option(
    "--strategy",
    type=click.Choice(list(STRATEGIES.keys())),
    prompt="Choose strategy",
    help="Trading strategy to use",
)
@click.option(
    "--start-date", prompt="Start date (YYYY-MM-DD)", help="Backtest start date"
)
@click.option("--end-date", prompt="End date (YYYY-MM-DD)", help="Backtest end date")
@click.option(
    "--interval",
    type=click.Choice(["1m", "5m", "15m", "30m", "1h", "1d", "1wk"]),
    default="1d",
    help="Data interval",
)
@click.option("--capital", type=float, default=100000, help="Initial capital")
def backtest(
    symbol: str,
    asset_type: str,
    strategy: str,
    start_date: str,
    end_date: str,
    interval: str,
    capital: float,
):
    """Run backtest with specified parameters."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        try:
            # Initialize components
            progress.add_task("Initializing...", total=None)
            asset = Asset(symbol, AssetType(asset_type))
            strategy_instance = STRATEGIES[strategy](params={})
            engine = BacktestEngine(initial_capital=capital)

            # Run backtest
            progress.add_task("Running backtest...", total=None)
            metrics = engine.run(
                strategy=strategy_instance,
                asset=asset,
                start_date=pd.Timestamp(start_date),
                end_date=pd.Timestamp(end_date),
                interval=interval,
            )

            # Display results
            _display_results(metrics, asset, strategy_instance)

        except Exception as e:
            console.print(f"[red]Error: {str(e)}")
            raise click.Abort()


def _display_results(metrics, asset, strategy):
    """Display backtest results in a formatted table."""
    table = Table(title=f"Backtest Results - {asset.symbol} ({strategy.name})")

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta", justify="right")

    # Add metrics to table
    table.add_row("Total Return", f"{metrics.total_return:.2f}%")
    table.add_row("Annual Return", f"{metrics.annual_return:.2f}%")
    table.add_row("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}")
    table.add_row("Max Drawdown", f"{metrics.max_drawdown:.2f}%")
    table.add_row("Total Trades", str(metrics.total_trades))
    table.add_row("Win Rate", f"{metrics.win_rate * 100:.2f}%")
    table.add_row("Average Win", f"${metrics.avg_win:.2f}")
    table.add_row("Average Loss", f"${metrics.avg_loss:.2f}")
    table.add_row("Volatility", f"{metrics.volatility:.2f}%")

    console.print(table)


@cli.command()
@click.argument("symbol")
def info(symbol: str):
    """Display basic information about an asset."""
    try:
        from ..data.fetcher import DataFetcher

        fetcher = DataFetcher()
        data = fetcher.get_data(
            Asset(symbol, AssetType.STOCK),
            start_date=pd.Timestamp.now() - pd.Timedelta(days=30),
            end_date=pd.Timestamp.now(),
            interval="1d",
        )

        table = Table(title=f"Asset Information - {symbol}")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        latest = data.iloc[-1]
        table.add_row("Current Price", f"${latest['Close']:.2f}")
        table.add_row(
            "Daily Change", f"{(latest['Close']/data.iloc[-2]['Close'] - 1)*100:.2f}%"
        )
        table.add_row("Volume", f"{latest['Volume']:,.0f}")
        table.add_row("30-Day High", f"${data['High'].max():.2f}")
        table.add_row("30-Day Low", f"${data['Low'].min():.2f}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        raise click.Abort()


if __name__ == "__main__":
    cli()
