from dataclasses import dataclass
from datetime import datetime

from app.domain.provenance import Provenance


@dataclass(frozen=True)
class ValuationSnapshot:
    """What the fundamentals provider reports about one security.

    `reading` is when the data was actually read, and from where. A
    snapshot replayed from cache keeps its original observation time, so
    nothing downstream can mistake yesterday's fundamentals for today's.
    """

    forward_pe: float | None
    trailing_pe: float | None
    peg_ratio: float | None
    dividend_yield: float | None

    market_cap: float | None = None
    eps: float | None = None

    #: What a token has instead of a balance sheet: how much of it exists,
    #: how much ever will, how much changes hands, and how long it has.
    circulating_supply: float | None = None
    max_supply: float | None = None
    volume_24h: float | None = None
    inception: datetime | None = None

    #: Company fundamentals, all as decimal ratios (0.12 is 12%) and all read
    #: from the same provider call as the valuation above. A company has these
    #: where a token has the supply fields. `debt_to_equity` and
    #: `current_ratio` are plain ratios; the cash flows are absolute amounts
    #: in the reporting currency, read for their sign more than their size.
    revenue_growth: float | None = None
    earnings_growth: float | None = None
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    current_ratio: float | None = None
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None
    sector: str | None = None
    industry: str | None = None

    reading: Provenance | None = None

    @property
    def observed_at(self) -> datetime | None:
        """When this was read, if it says."""

        return self.reading.observed_at if self.reading is not None else None
