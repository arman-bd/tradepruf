from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass
class Position:
    """Represents a trading position."""

    symbol: str
    entry_price: Decimal
    entry_date: datetime
    shares: int
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    exit_price: Decimal | None = None
    exit_date: datetime | None = None

    @property
    def is_open(self) -> bool:
        return self.exit_price is None

    @property
    def duration(self) -> int | None:
        if not self.exit_date:
            return None
        return (self.exit_date - self.entry_date).days

    @property
    def profit_loss(self) -> Decimal | None:
        if not self.exit_price:
            return None
        return (self.exit_price - self.entry_price) * self.shares

    @property
    def profit_loss_pct(self) -> Decimal | None:
        if not self.profit_loss:
            return None
        return (self.profit_loss / (self.entry_price * self.shares)) * 100
