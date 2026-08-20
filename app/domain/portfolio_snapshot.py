from dataclasses import dataclass
from datetime import datetime

from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.portfolio_position import PortfolioPosition


@dataclass(frozen=True, slots=True)
class Allocation:
    #: The share of the account held in cash, or **None where the broker
    #: did not state a cash figure**.
    #:
    #: An unavailable cash reading is not a zero one. A zero here says
    #: the account measurably holds no cash; None says nobody could read
    #: it. Collapsing the second into the first told the investor the
    #: account was fully deployed, and told the capital envelope that
    #: the portfolio had no room — both claims about an account, built
    #: out of an absence.
    cash: float | None

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
    #: Absent where no rate has been read. A conversion is derived
    #: from a measurement, and without one it is not filled in.
    total_value_eur: float | None = None

    # Real dashboard values.

    #: Cash in account currency, or None where the broker did not state
    #: it. See `Allocation.cash` — absence is preserved, never zeroed.
    available_cash_usd: float | None = None

    available_cash_eur: float | None = None
    invested_usd: float = 0.0
    invested_eur: float | None = None

    #: The same reading as `Allocation.cash`, expressed as the account's
    #: liquid share. None for the same reason, and never 0.0 for it.
    liquidity_pct: float | None = None

    #: **The moment MOVRvest received a successful account response from
    #: eToro — not the time eToro observed the account.**
    #:
    #: eToro states no account observation time: the `pnl` route's
    #: `ClientPortfolio` carries thirteen top-level properties and none
    #: is temporal, and the balances route carries none either (the
    #: eToro MCP read-only acceptance measured this, 2026-08-20). Every
    #: timestamp that route does return belongs to a position or an
    #: order.
    #:
    #: This value is therefore usable as an **operational freshness
    #: gate** — it bounds how long ago this platform last succeeded in
    #: reaching the broker — and it must never be presented as the
    #: account's `asOf`, the broker's snapshot time or the source
    #: timestamp. **Freshness of receipt does not establish the age of
    #: eToro's underlying account state.**
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
