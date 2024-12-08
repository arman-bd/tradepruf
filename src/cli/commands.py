import json

import click
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from src.strategies.base import Strategy

from ..backtest.engine import BacktestEngine
from ..core.asset import Asset, AssetType
from ..strategies.momentum import MACDStrategy, RSIStrategy
from ..strategies.moving_average import EMAStrategy, SMACrossoverStrategy
from ..strategies.volatility import ATRTrailingStopStrategy, BollingerBandsStrategy
from ..visualization.charts import BacktestVisualizer

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
@click.option(
    "--charts",
    type=click.Choice(["none", "html", "png", "interactive"]),
    default="none",
    help="Generate charts in specified format",
)
@click.option(
    "--output-dir", type=str, default="charts", help="Directory to save charts"
)
def backtest(
    symbol: str,
    asset_type: str,
    strategy: str,
    start_date: str,
    end_date: str,
    interval: str,
    capital: float,
    charts: str,
    output_dir: str,
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
            result = engine.run(
                strategy=strategy_instance,
                asset=asset,
                start_date=pd.Timestamp(start_date),
                end_date=pd.Timestamp(end_date),
                interval=interval,
            )

            # Create visualizations if requested
            if charts != "none":
                visualizer = BacktestVisualizer(output_dir)

                # Convert positions to dict format for visualization
                trade_info = [
                    {
                        "symbol": p.symbol,
                        "entry_date": p.entry_date,
                        "entry_price": float(p.entry_price),
                        "exit_date": p.exit_date,
                        "exit_price": float(p.exit_price) if p.exit_price else None,
                        "shares": float(p.shares),
                    }
                    for p in result.metrics.closed_positions
                ]

                # Create charts
                visualizer.create_equity_curve(
                    result.equity_series,
                    trade_info,
                    f"{symbol} Equity Curve",
                    format=charts,
                )
                visualizer.create_drawdown_chart(result.equity_series, format=charts)
                visualizer.create_monthly_returns_heatmap(
                    result.equity_series, format=charts
                )

                print(f"\nCharts have been saved to {output_dir}/")

            # Display results
            _display_results(result.metrics, asset, strategy_instance)

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


@cli.command()
@click.option("--portfolio", type=str, help="Portfolio config file path")
@click.option(
    "--charts",
    type=click.Choice(["none", "html", "png", "interactive"]),
    default="none",
    help="Generate charts in specified format",
)
@click.option(
    "--output-dir", type=str, default="charts", help="Directory to save charts"
)
def backtest_portfolio(portfolio: str, charts: str, output_dir: str):
    """Run backtest with a portfolio of assets."""
    try:
        # Load portfolio configuration
        with open(portfolio) as f:
            config = json.load(f)

        assets = []
        strategies = {}

        for asset_config in config["assets"]:
            symbol = asset_config["symbol"]
            asset_type = asset_config["type"]
            strategy_type = asset_config["strategy"]

            asset = Asset(symbol, AssetType(asset_type))
            assets.append(asset)

            # Create strategy instance
            strategy = STRATEGIES[strategy_type](params=asset_config.get("params", {}))
            strategies[symbol] = strategy

        # Initialize engine
        engine = BacktestEngine(
            initial_capital=config.get("initial_capital", 100000),
            position_size=config.get("position_size", 0.1),
            max_positions=config.get("max_positions", 5),
        )

        # Run portfolio backtest
        result = engine.run_portfolio(
            strategies=strategies,
            assets=assets,
            start_date=pd.Timestamp(config["start_date"]),
            end_date=pd.Timestamp(config["end_date"]),
            interval=config.get("interval", "1d"),
        )

        # Create visualizations if requested
        if charts != "none":
            visualizer = BacktestVisualizer(output_dir)

            # Convert positions to dict format for visualization
            trade_info = [
                {
                    "symbol": p.symbol,
                    "entry_date": p.entry_date,
                    "entry_price": float(p.entry_price),
                    "exit_date": p.exit_date,
                    "exit_price": float(p.exit_price) if p.exit_price else None,
                    "shares": float(p.shares),
                    "current_price": float(p.exit_price or p.entry_price),
                }
                for p in result.metrics.closed_positions
            ]

            # Create charts
            visualizer.create_equity_curve(
                result.equity_series,
                trade_info,
                "Portfolio Equity Curve",
                format=charts,
            )
            visualizer.create_drawdown_chart(result.equity_series, format=charts)
            visualizer.create_monthly_returns_heatmap(
                result.equity_series, format=charts
            )
            visualizer.create_asset_allocation(trade_info, format=charts)

            print(f"\nCharts have been saved to {output_dir}/")

        _display_portfolio_results(result.metrics, assets, strategies)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}")
        raise click.Abort()


def _display_portfolio_results(
    metrics, assets: list[Asset], strategies: dict[str, Strategy]
):
    """Display portfolio backtest results in a formatted table."""
    table = Table(title="Portfolio Backtest Results")

    table.add_column("Metric", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta", justify="right")

    # Add portfolio metrics
    table.add_row("Total Return", f"{float(metrics.total_return):.2f}%")
    table.add_row("Annual Return", f"{float(metrics.annual_return):.2f}%")
    table.add_row("Sharpe Ratio", f"{float(metrics.sharpe_ratio):.2f}")
    table.add_row("Max Drawdown", f"{float(metrics.max_drawdown):.2f}%")
    table.add_row("Total Trades", str(metrics.total_trades))
    table.add_row("Win Rate", f"{float(metrics.win_rate) * 100:.2f}%")
    table.add_row("Average Win", f"${float(metrics.avg_win):.2f}")
    table.add_row("Average Loss", f"${float(metrics.avg_loss):.2f}")
    table.add_row("Volatility", f"{float(metrics.volatility):.2f}%")

    console.print(table)

    # Display per-asset summary
    asset_table = Table(title="Asset Performance Summary")
    asset_table.add_column("Asset", style="cyan")
    asset_table.add_column("Strategy", style="blue")
    asset_table.add_column("Type", style="green")
    asset_table.add_column("Trades", justify="right")
    asset_table.add_column("P&L", justify="right", style="magenta")

    for asset in assets:
        asset_positions = [
            p for p in metrics.closed_positions if p.symbol == asset.symbol
        ]
        strategy = strategies[asset.symbol]
        total_pnl = sum(p.profit_loss for p in asset_positions)

        asset_table.add_row(
            asset.symbol,
            strategy.name,
            asset.asset_type.value,
            str(len(asset_positions)),
            f"${float(total_pnl):,.2f}",
        )

    console.print("\n")
    console.print(asset_table)


if __name__ == "__main__":
    cli()
