from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class PortfolioFacts:
    total_value_usd: float
    total_value_eur: float | None

    cash_usd: float
    invested_usd: float
    unrealized_pnl_usd: float

    #: None where the broker stated no cash figure.
    cash_allocation: float | None
    positions: int
    pending_orders: int
    copy_portfolios: int

    connected: bool
    latency_ms: float
    last_sync: datetime
    source: str
