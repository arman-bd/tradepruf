from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Position:
    """Represents a trading position with leverage support."""

    symbol: str
    entry_price: Decimal
    entry_date: datetime
    shares: Decimal
    leverage: Decimal = Decimal('1')  # Default leverage is 1x
    spread_fee: Decimal = Decimal('0')  # Spread fee per share
    liquidation_price: Decimal | None = None
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
    def position_value(self) -> Decimal:
        """Calculate the actual position value including leverage."""
        return self.shares * self.entry_price * self.leverage
    
    @property
    def margin_required(self) -> Decimal:
        """Calculate required margin for the position."""
        return self.position_value / self.leverage

    @property
    def profit_loss(self) -> Decimal | None:
        """Calculate P&L including leverage and spread fees."""
        if not self.exit_price:
            return None
        
        # Calculate raw P&L with leverage
        raw_pl = (self.exit_price - self.entry_price) * self.shares * self.leverage
        
        # Subtract spread fees (applied to both entry and exit)
        total_spread_cost = self.spread_fee * self.shares * Decimal('2')
        
        return raw_pl - total_spread_cost

    @property
    def profit_loss_pct(self) -> Decimal | None:
        if not self.profit_loss:
            return None
        return (self.profit_loss / self.margin_required) * 100

    def check_liquidation(self, current_price: Decimal) -> bool:
        """Check if position should be liquidated based on current price."""
        if self.liquidation_price is None:
            return False
        
        if self.leverage > Decimal('1'):
            return current_price <= self.liquidation_price
        
        return False