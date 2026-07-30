from dataclasses import dataclass
from datetime import datetime

from app.domain.portfolio_position import PortfolioPosition


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    broker: str
    mode: str
    connected: bool

    positions_count: int
    positions: tuple[PortfolioPosition, ...]

    pending_orders: int
    copy_portfolios: int
    latency_ms: float
    timestamp: datetime

    cash_usd: float | None = None
    invested_usd: float | None = None
    unrealized_pnl_usd: float | None = None
    equity_usd: float | None = None
