from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns


class BacktestVisualizer:
    def __init__(self, output_dir: str = "charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def create_equity_curve(
        self,
        equity_series: pd.Series,
        trades: list[dict],
        title: str,
        format: str = "html",
    ):
        """Create equity curve with trade markers."""
        # Create figure
        fig = go.Figure()

        # Add equity curve
        fig.add_trace(
            go.Scatter(
                x=equity_series.index,
                y=equity_series.values,
                name="Portfolio Value",
                line={"color": "blue"},
            )
        )

        # Add trade markers
        buy_dates = [t["entry_date"] for t in trades]
        buy_prices = [t["entry_price"] for t in trades]
        sell_dates = [t["exit_date"] for t in trades if t["exit_date"]]
        sell_prices = [t["exit_price"] for t in trades if t["exit_price"]]

        fig.add_trace(
            go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode="markers",
                name="Buy",
                marker={"color": "green", "size": 10, "symbol": "triangle-up"},
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode="markers",
                name="Sell",
                marker={"color": "red", "size": 10, "symbol": "triangle-down"},
            )
        )

        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
        )

        # Save based on format
        if format == "html":
            fig.write_html(
                self.output_dir
                / f"equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "png":
            fig.write_image(
                self.output_dir
                / f"equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
        elif format == "interactive":
            fig.show()

    def create_drawdown_chart(self, equity_series: pd.Series, format: str = "html"):
        """Create drawdown visualization."""
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak * 100

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=drawdown.index, y=drawdown.values, fill="tozeroy", name="Drawdown"
            )
        )

        fig.update_layout(
            title="Portfolio Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode="x unified",
        )

        if format == "html":
            fig.write_html(
                self.output_dir
                / f"drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "png":
            fig.write_image(
                self.output_dir
                / f"drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
        elif format == "interactive":
            fig.show()

    def create_monthly_returns_heatmap(
        self, equity_series: pd.Series, format: str = "html"
    ):
        """Create monthly returns heatmap."""
        # Calculate monthly returns
        monthly_returns = equity_series.resample("ME").last().pct_change() * 100
        returns_by_month = monthly_returns.groupby(
            [monthly_returns.index.year, monthly_returns.index.month]
        ).first()
        returns_matrix = returns_by_month.unstack()

        if format in ["html", "interactive"]:
            fig = px.imshow(
                returns_matrix,
                labels={"x": "Month", "y": "Year", "color": "Returns (%)"},
                title="Monthly Returns Heatmap",
            )

            if format == "html":
                fig.write_html(
                    self.output_dir
                    / f"monthly_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                )
            else:
                fig.show()
        else:
            plt.figure(figsize=(12, 8))
            sns.heatmap(returns_matrix, annot=True, fmt=".1f", cmap="RdYlGn", center=0)
            plt.title("Monthly Returns Heatmap")
            plt.savefig(
                self.output_dir
                / f"monthly_returns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            plt.close()

    def create_asset_allocation(self, positions: list[dict], format: str = "html"):
        """Create asset allocation pie chart."""
        asset_values = {}
        for pos in positions:
            if pos["symbol"] not in asset_values:
                asset_values[pos["symbol"]] = 0
            asset_values[pos["symbol"]] += float(pos["shares"]) * float(
                pos["current_price"]
            )

        if format in ["html", "interactive"]:
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=list(asset_values.keys()),
                        values=list(asset_values.values()),
                    )
                ]
            )

            if format == "html":
                fig.write_html(
                    self.output_dir
                    / f"allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                )
            else:
                fig.show()
        else:
            plt.figure(figsize=(10, 10))
            plt.pie(
                list(asset_values.values()),
                labels=list(asset_values.keys()),
                autopct="%1.1f%%",
            )
            plt.title("Asset Allocation")
            plt.savefig(
                self.output_dir
                / f"allocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            plt.close()
