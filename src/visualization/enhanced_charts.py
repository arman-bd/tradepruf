from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots

from src.visualization.charts import BacktestVisualizer


class EnhancedBacktestVisualizer(BacktestVisualizer):
    """Enhanced visualization class with additional analysis capabilities."""

    def create_correlation_matrix(
        self, portfolio_returns: Dict[str, pd.Series], format: str = "html"
    ) -> go.Figure:
        """Create correlation matrix heatmap of asset returns."""
        # Combine all returns into a DataFrame
        returns_df = pd.DataFrame(portfolio_returns)

        # Calculate correlation matrix
        corr_matrix = returns_df.corr()

        # Create figure
        fig = go.Figure(
            data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                colorscale="RdBu",
                zmin=-1,
                zmax=1,
            )
        )

        fig.update_layout(
            title="Asset Returns Correlation Matrix",
            xaxis_title="Asset",
            yaxis_title="Asset",
            width=800,
            height=800,
        )

        # Handle file saving and display based on format
        if format == "html":
            fig.write_html(
                self.output_dir
                / f"correlation_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "png":
            plt.figure(figsize=(10, 8))
            sns.heatmap(corr_matrix, annot=True, cmap="RdBu", center=0, vmin=-1, vmax=1)
            plt.title("Asset Returns Correlation Matrix")
            plt.tight_layout()
            plt.savefig(
                self.output_dir
                / f"correlation_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
            plt.close()
        elif format == "interactive":
            fig.show()

        return fig

    def create_interactive_pair_comparison(
        self, portfolio_data: Dict[str, pd.Series], format: str = "html"
    ) -> go.Figure:
        """Create an interactive pair-wise comparison dashboard for all assets."""
        assets = list(portfolio_data.keys())

        # Pre-calculate normalized prices and returns for all assets
        normalized_prices = {}
        returns = {}
        for symbol, data in portfolio_data.items():
            normalized_prices[symbol] = data / data.iloc[0] * 100
            returns[symbol] = data.pct_change()

        # Create the main figure with dropdown menus
        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=(
                "Normalized Performance Comparison",
                "30-Day Rolling Correlation",
                "Return Scatter Plot",
            ),
            vertical_spacing=0.1,
            specs=[[{"secondary_y": True}], [{}], [{}]],
        )

        # Add dropdown menus for asset selection
        updatemenus = [
            dict(
                buttons=list(
                    [
                        dict(
                            args=[
                                {
                                    "visible": [
                                        i == j or i == j + len(assets)
                                        for i in range(len(assets) * 2)
                                    ]
                                }
                            ],
                            label=f"Asset 1: {asset}",
                            method="update",
                        )
                        for j, asset in enumerate(assets)
                    ]
                ),
                direction="down",
                showactive=True,
                x=0.1,
                xanchor="left",
                y=1.15,
                yanchor="top",
            ),
            dict(
                buttons=list(
                    [
                        dict(
                            args=[
                                {
                                    "visible": [
                                        i == j or i == j + len(assets)
                                        for i in range(len(assets) * 2)
                                    ]
                                }
                            ],
                            label=f"Asset 2: {asset}",
                            method="update",
                        )
                        for j, asset in enumerate(assets)
                    ]
                ),
                direction="down",
                showactive=True,
                x=0.3,
                xanchor="left",
                y=1.15,
                yanchor="top",
            ),
        ]

        # Add traces for all possible pairs
        for i, asset1 in enumerate(assets):
            for j, asset2 in enumerate(assets):
                if i != j:
                    norm1 = normalized_prices[asset1]
                    norm2 = normalized_prices[asset2]
                    rolling_corr = (
                        returns[asset1].rolling(window=30).corr(returns[asset2])
                    )

                    # Add traces
                    for data, row, color, name in [
                        ((norm1, "Values"), 1, "blue", f"{asset1} Price"),
                        ((norm2, "Values"), 1, "red", f"{asset2} Price"),
                        ((rolling_corr, "Values"), 2, "green", "Rolling Correlation"),
                        (
                            (returns[asset1], returns[asset2]),
                            3,
                            "purple",
                            "Daily Returns",
                        ),
                    ]:
                        if len(data) == 2 and isinstance(data[1], pd.Series):
                            # Scatter plot for returns
                            fig.add_trace(
                                go.Scatter(
                                    x=data[0],
                                    y=data[1],
                                    mode="markers",
                                    name=name,
                                    visible=(i == 0 and j == 1),
                                    marker=dict(size=5, color=color, opacity=0.5),
                                ),
                                row=row,
                                col=1,
                            )
                        else:
                            # Line plots for other data
                            fig.add_trace(
                                go.Scatter(
                                    x=data[0].index,
                                    y=data[0].values,
                                    name=name,
                                    visible=(i == 0 and j == 1),
                                    line=dict(color=color),
                                ),
                                row=row,
                                col=1,
                            )

        # Update layout
        fig.update_layout(
            height=1200,
            showlegend=True,
            title_text="Interactive Pair-wise Asset Comparison",
            updatemenus=updatemenus,
            hovermode="x unified",
        )

        # Update axes labels
        for row, (x_title, y_title) in enumerate(
            [
                ("Date", "Normalized Value"),
                ("Date", "Correlation"),
                ("Asset 1 Returns", "Asset 2 Returns"),
            ],
            1,
        ):
            fig.update_xaxes(title_text=x_title, row=row, col=1)
            fig.update_yaxes(title_text=y_title, row=row, col=1)

        if format == "html":
            fig.write_html(
                self.output_dir
                / f"interactive_pair_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "interactive":
            fig.show()

        return fig

    def create_portfolio_risk_analysis(
        self,
        returns_data: Dict[str, pd.Series],
        weights: Optional[Dict[str, float]] = None,
        format: str = "html",
    ) -> go.Figure:
        """Create portfolio risk analysis visualization."""
        returns_df = pd.DataFrame(returns_data)
        weights = weights or {
            col: 1.0 / len(returns_df.columns) for col in returns_df.columns
        }

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_metrics(returns_df, weights)
        risk_contributions = self._calculate_risk_contributions(
            returns_df, weights, portfolio_metrics["portfolio_vol"]
        )

        # Create visualization
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Asset Weights",
                "Risk Contributions",
                "Rolling Portfolio Volatility",
                "Rolling Correlations",
            ),
            specs=[
                [{"type": "domain"}, {"type": "domain"}],
                [{"type": "xy"}, {"type": "xy"}],
            ],
        )

        # Add weight pie chart
        fig.add_trace(
            go.Pie(
                labels=list(weights.keys()),
                values=list(weights.values()),
                name="Weights",
            ),
            row=1,
            col=1,
        )

        # Add risk contribution pie chart
        fig.add_trace(
            go.Pie(
                labels=list(risk_contributions.keys()),
                values=list(risk_contributions.values()),
                name="Risk",
            ),
            row=1,
            col=2,
        )

        # Add rolling portfolio volatility
        rolling_vol = returns_df.mul(list(weights.values())).sum(axis=1).rolling(
            window=30
        ).std() * np.sqrt(252)
        fig.add_trace(
            go.Scatter(
                x=rolling_vol.index, y=rolling_vol.values, name="Portfolio Volatility"
            ),
            row=2,
            col=1,
        )

        # Add rolling correlations
        assets = list(weights.keys())
        for i in range(len(assets) - 1):
            for j in range(i + 1, len(assets)):
                rolling_corr = (
                    returns_df[assets[i]].rolling(30).corr(returns_df[assets[j]])
                )
                fig.add_trace(
                    go.Scatter(
                        x=rolling_corr.index,
                        y=rolling_corr.values,
                        name=f"{assets[i]} vs {assets[j]}",
                    ),
                    row=2,
                    col=2,
                )

        # Update layout
        fig.update_layout(
            height=1000,
            width=1200,
            title_text="Portfolio Risk Analysis",
            showlegend=True,
        )

        if format == "html":
            fig.write_html(
                self.output_dir
                / f"portfolio_risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "png":
            fig.write_image(
                self.output_dir
                / f"portfolio_risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
        elif format == "interactive":
            fig.show()

        return fig

    def create_trade_analysis(
        self, trades: List[Dict], format: str = "html"
    ) -> go.Figure:
        """Create detailed trade analysis visualization."""
        trades_df = pd.DataFrame(trades)
        trades_df["entry_date"] = pd.to_datetime(trades_df["entry_date"], utc=True)
        trades_df["exit_date"] = pd.to_datetime(trades_df["exit_date"], utc=True)
        trades_df["duration"] = trades_df["exit_date"] - trades_df["entry_date"]
        trades_df["return"] = (
            (trades_df["exit_price"] - trades_df["entry_price"])
            / trades_df["entry_price"]
            * 100
        )

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Returns Distribution",
                "Trade Duration vs Returns",
                "Cumulative Returns by Symbol",
                "Monthly Trade Frequency",
            ),
        )

        # Add returns distribution
        fig.add_trace(
            go.Histogram(x=trades_df["return"], name="Returns Distribution"),
            row=1,
            col=1,
        )

        # Add duration vs returns scatter
        fig.add_trace(
            go.Scatter(
                x=trades_df["duration"].dt.days,
                y=trades_df["return"],
                mode="markers",
                name="Duration vs Returns",
            ),
            row=1,
            col=2,
        )

        # Add cumulative returns by symbol
        for symbol in trades_df["symbol"].unique():
            symbol_trades = trades_df[trades_df["symbol"] == symbol]
            cumulative_returns = (1 + symbol_trades["return"] / 100).cumprod()
            fig.add_trace(
                go.Scatter(
                    x=list(range(len(cumulative_returns))),
                    y=cumulative_returns,
                    name=f"{symbol} Cumulative",
                ),
                row=2,
                col=1,
            )

        # Add monthly trade frequency
        monthly_trades = trades_df.set_index("entry_date").resample("ME").size()
        fig.add_trace(
            go.Bar(
                x=monthly_trades.index, y=monthly_trades.values, name="Monthly Trades"
            ),
            row=2,
            col=2,
        )

        # Update layout
        fig.update_layout(
            height=1000,
            width=1200,
            title_text="Detailed Trade Analysis",
            showlegend=True,
        )

        # Update axes labels
        for row, col, x_title, y_title in [
            (1, 1, "Return (%)", "Frequency"),
            (1, 2, "Duration (days)", "Return (%)"),
            (2, 1, "Trade Number", "Cumulative Return"),
            (2, 2, "Date", "Number of Trades"),
        ]:
            fig.update_xaxes(title_text=x_title, row=row, col=col)
            fig.update_yaxes(title_text=y_title, row=row, col=col)

        if format == "html":
            fig.write_html(
                self.output_dir
                / f"trade_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "png":
            fig.write_image(
                self.output_dir
                / f"trade_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            )
        elif format == "interactive":
            fig.show()

        return fig

    def _calculate_portfolio_metrics(
        self, returns_df: pd.DataFrame, weights: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate portfolio metrics."""
        portfolio_return = sum(
            returns_df[asset].mean() * weight for asset, weight in weights.items()
        )
        portfolio_vol = np.sqrt(
            sum(
                sum(
                    weights[asset1]
                    * weights[asset2]
                    * returns_df[asset1].cov(returns_df[asset2])
                    for asset2 in weights.keys()
                )
                for asset1 in weights.keys()
            )
        )
        return {"portfolio_return": portfolio_return, "portfolio_vol": portfolio_vol}

    def _calculate_risk_contributions(
        self, returns_df: pd.DataFrame, weights: Dict[str, float], portfolio_vol: float
    ) -> Dict[str, float]:
        """Calculate risk contributions for each asset."""
        risk_contributions = {}
        for asset in weights.keys():
            marginal_contrib = sum(
                weights[other_asset] * returns_df[asset].cov(returns_df[other_asset])
                for other_asset in weights.keys()
            )
            risk_contributions[asset] = (
                weights[asset] * marginal_contrib / portfolio_vol
            )
        return risk_contributions

    def create_equity_curve(
        self, equity_series: pd.Series, trades: List[Dict], format: str = "html"
    ) -> go.Figure:
        """Create equity curve with trade markers."""
        fig = go.Figure()

        # Add equity curve
        fig.add_trace(
            go.Scatter(
                x=equity_series.index,
                y=equity_series.values,
                name="Portfolio Value",
                line=dict(color="blue"),
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
                text=[f"{t['symbol']} Buy" for t in trades],
                marker={"color": "green", "size": 10, "symbol": "triangle-up"},
            )
        )

        fig.add_trace(
            go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode="markers",
                name="Sell",
                text=[f"{t['symbol']} Sell" for t in trades],
                marker={"color": "red", "size": 10, "symbol": "triangle-down"},
            )
        )

        # Update layout
        fig.update_layout(
            title="Portfolio Equity Curve",
            xaxis_title="Date",
            yaxis_title="Portfolio Value ($)",
            hovermode="x unified",
            height=400,
        )

        if format == "html":
            fig.write_html(
                self.output_dir
                / f"equity_curve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "interactive":
            fig.show()

        return fig

    def create_drawdown_chart(
        self, equity_series: pd.Series, format: str = "html"
    ) -> go.Figure:
        """Create drawdown visualization."""
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak * 100

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=drawdown.index,
                y=drawdown.values,
                fill="tozeroy",
                name="Drawdown",
                line=dict(color="red"),
            )
        )

        fig.update_layout(
            title="Portfolio Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            hovermode="x unified",
            height=400,
        )

        if format == "html":
            fig.write_html(
                self.output_dir
                / f"drawdown_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            )
        elif format == "interactive":
            fig.show()

        return fig

    def create_monthly_returns_heatmap(
        self, equity_series: pd.Series, format: str = "html"
    ) -> go.Figure:
        """Create monthly returns heatmap."""
        equity_series.index = pd.to_datetime(equity_series.index, utc=True)
        monthly_returns = equity_series.resample("ME").last().pct_change() * 100
        returns_by_month = monthly_returns.groupby(
            [monthly_returns.index.year, monthly_returns.index.month]
        ).first()
        returns_matrix = returns_by_month.unstack()

        fig = go.Figure(
            data=go.Heatmap(
                z=returns_matrix.values,
                x=returns_matrix.columns,
                y=returns_matrix.index,
            )
        )

        if format == "html":
            fig.write_html(f"monthly_returns_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        elif format == "interactive":
            fig.show()

        return fig
