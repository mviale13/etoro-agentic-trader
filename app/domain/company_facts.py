from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompanyFacts:
    instrument_id: int

    symbol: str
    name: str

    asset_type: str
    exchange: str

    # Market
    current_price: float | None
    daily_change_pct: float | None
    market_cap: float | None

    # Valuation
    forward_pe: float | None

    # Growth
    revenue_growth: float | None = None
    earnings_growth: float | None = None

    # Profitability
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None

    # Capital efficiency
    roe: float | None = None
    roic: float | None = None

    # Balance sheet
    debt_to_equity: float | None = None
    current_ratio: float | None = None

    # Cash generation
    free_cash_flow: float | None = None

    # Shareholder returns
    eps: float | None = None
    dividend_yield: float | None = None

    # Classification
    sector: str | None = None
    industry: str | None = None
