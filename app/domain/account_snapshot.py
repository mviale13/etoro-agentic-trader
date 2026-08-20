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

    #: **The moment MOVRvest received this successful account response**
    #: — not the moment eToro observed the account.
    #:
    #: eToro states no account observation time: the `pnl` route returns
    #: `ClientPortfolio`, whose thirteen top-level properties contain
    #: nothing temporal, and every timestamp it does carry belongs to a
    #: position or an order. It is usable as an operational freshness
    #: gate and must never be presented as the account's `asOf`, the
    #: broker's snapshot time or the source timestamp.
    timestamp: datetime

    cash_usd: float | None = None
    invested_usd: float | None = None
    unrealized_pnl_usd: float | None = None
    equity_usd: float | None = None
