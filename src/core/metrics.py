from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd

from .position import Position
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetrics:
    """Trading performance metrics"""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    max_drawdown: Decimal
    sharpe_ratio: Decimal
    total_return: Decimal
    annual_return: Decimal
    volatility: Decimal
    closed_positions: list[Position]  # Add this field

    @classmethod
    def empty(cls):
        """Create empty metrics with zero values."""
        return cls(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=Decimal("0"),
            avg_win=Decimal("0"),
            avg_loss=Decimal("0"),
            max_drawdown=Decimal("0"),
            sharpe_ratio=Decimal("0"),
            total_return=Decimal("0"),
            annual_return=Decimal("0"),
            volatility=Decimal("0"),
            closed_positions=[],  # Add empty list for closed positions
        )


class MetricsCalculator:
    """Calculates trading performance metrics."""

    @staticmethod
    def calculate_metrics(
        positions: list[Position], equity_curve: pd.Series
    ) -> PerformanceMetrics:
        try:
            closed_positions = [p for p in positions if not p.is_open]

            if not closed_positions or len(equity_curve) < 2:
                return PerformanceMetrics.empty()

            # Basic metrics
            total_trades = len(closed_positions)
            winning_trades = len([p for p in closed_positions if p.profit_loss > 0])
            losing_trades = total_trades - winning_trades

            # Win rate and averages
            win_rate = (
                Decimal(winning_trades) / Decimal(total_trades)
                if total_trades > 0
                else Decimal("0")
            )

            winning_pls = [p.profit_loss for p in closed_positions if p.profit_loss > 0]
            losing_pls = [p.profit_loss for p in closed_positions if p.profit_loss < 0]

            avg_win = (
                sum(winning_pls) / len(winning_pls) if winning_pls else Decimal("0")
            )
            avg_loss = sum(losing_pls) / len(losing_pls) if losing_pls else Decimal("0")

            # Calculate returns directly from equity values
            first_equity = float(equity_curve.iloc[0])
            last_equity = float(equity_curve.iloc[-1])

            # Calculate percentage returns
            total_return = Decimal(
                str((last_equity - first_equity) / first_equity * 100)
            )

            # Calculate daily returns for volatility and other metrics
            daily_returns = pd.Series(
                [
                    (equity_curve.iloc[i] - equity_curve.iloc[i - 1])
                    / equity_curve.iloc[i - 1]
                    for i in range(1, len(equity_curve))
                ]
            )

            # Calculate max drawdown
            peak = equity_curve.expanding(min_periods=1).max()
            drawdown = (equity_curve - peak) / peak
            max_drawdown = Decimal(str(abs(float(drawdown.min()) * 100)))

            # Calculate annual metrics
            days = (equity_curve.index[-1] - equity_curve.index[0]).days
            annualization_factor = Decimal("365") / Decimal(str(max(days, 1)))

            # Calculate annualized return using CAGR formula
            annual_return = (
                (Decimal(str(last_equity)) / Decimal(str(first_equity)))
                ** annualization_factor
                - Decimal("1")
            ) * Decimal("100")

            # Calculate annualized volatility
            daily_std = Decimal(str(daily_returns.std()))
            volatility = daily_std * Decimal(str(np.sqrt(252))) * Decimal("100")

            # Calculate Sharpe ratio using actual returns
            risk_free_rate = Decimal("0.02")  # 2% annual risk-free rate
            excess_return = annual_return / Decimal("100") - risk_free_rate
            sharpe_ratio = (
                excess_return / (volatility / Decimal("100"))
                if volatility != 0
                else Decimal("0")
            )

            return PerformanceMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                closed_positions=closed_positions,
            )

        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            import traceback

            traceback.print_exc()
            return PerformanceMetrics.empty()


def calculate_max_drawdown(equity_curve: pd.Series) -> float:
    rolling_max = equity_curve.expanding().max()
    drawdowns = equity_curve / rolling_max - 1
    return abs(float(drawdowns.min() * 100))


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    excess_returns = returns - risk_free_rate / 252
    return float(np.sqrt(252) * excess_returns.mean() / returns.std())
