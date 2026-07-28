from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompanyFacts:
    instrument_id: int

    symbol: str
    name: str

    asset_type: str

    exchange: str

    current_price: float | None

    daily_change_pct: float | None

    market_cap: float | None

    forward_pe: float | None

    eps: float | None

    dividend_yield: float | None

    sector: str | None

    industry: str | None
