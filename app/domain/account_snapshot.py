from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    broker: str
    mode: str
    connected: bool
    positions: int
    pending_orders: int
    copy_portfolios: int
    latency_ms: float
    timestamp: datetime
    cash_usd: float | None = None
    invested_usd: float | None = None
    unrealized_pnl_usd: float | None = None
    equity_usd: float | None = None
