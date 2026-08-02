from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ValuationSnapshot:
    """What the fundamentals provider reports about one company.

    `observed_at` is when the data was actually read from the provider, not
    when it was served. A snapshot replayed from cache keeps its original
    observation time, so nothing downstream can mistake yesterday's
    fundamentals for today's.
    """

    forward_pe: float | None
    trailing_pe: float | None
    peg_ratio: float | None
    dividend_yield: float | None

    market_cap: float | None = None
    eps: float | None = None

    observed_at: datetime | None = None
