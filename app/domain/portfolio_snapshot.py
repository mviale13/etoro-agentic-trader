from dataclasses import dataclass
from datetime import datetime

from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.portfolio_position import PortfolioPosition


@dataclass(frozen=True, slots=True)
class Allocation:
    cash: float
    stocks: float
    etfs: float
    crypto: float
    unclassified: float


@dataclass(frozen=True, slots=True)
class PortfolioSnapshot:
    allocation: Allocation
    total_value: float
    positions: int
    largest_position: str | None
    largest_position_pct: float
    risk_flags: tuple[str, ...]
    total_value_eur: float = 0.0

    # Real dashboard values.
    available_cash_usd: float = 0.0
    available_cash_eur: float = 0.0
    invested_usd: float = 0.0
    invested_eur: float = 0.0
    liquidity_pct: float = 0.0
    last_sync: datetime | None = None

    # The individual holdings behind `positions`. The Brain stores the facts
    # the broker actually reported, so reasoning can work per symbol.
    holdings: tuple[PortfolioPosition, ...] = ()
    pending_orders: int = 0
    unrealized_pnl_usd: float = 0.0

    # What this account has actually been through, which every other field
    # here is silent about: they all describe the present moment. None
    # where the broker's balance history was unreachable or too short to
    # measure, and never filled in with a figure derived from the holdings.
    drawdown: PortfolioDrawdown | None = None

    @property
    def total_value_usd(self) -> float:
        return self.total_value

    def weight_pct(self, holding: PortfolioPosition) -> float | None:
        """
        The holding's share of the account, or None when the account
        reports no value to take a share of. A weight nobody can compute
        is absent, not zero.
        """

        if self.total_value <= 0.0:
            return None

        return holding.market_value_usd / self.total_value * 100.0
