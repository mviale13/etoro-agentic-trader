from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class CompanyFacts:
    """Observable company data available at a specific point in time.

    Notes:
    - Percentage values are expressed as decimal ratios:
        0.12  -> 12%
       -0.05 -> -5%
    - Missing financial data is represented by None.
    """

    # Identity
    instrument_id: int
    symbol: str
    name: str

    # Classification
    asset_type: str
    exchange: str

    # Observation metadata
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    currency: str | None = None

    # Market
    current_price: float | None = None
    daily_change_pct: float | None = None
    market_cap: float | None = None

    # Risk, measured from the observed price history rather than assumed.
    #: Annualised standard deviation of daily returns, as a ratio.
    realized_volatility: float | None = None
    #: Deepest peak-to-trough fall observed, as a positive ratio.
    max_drawdown: float | None = None

    # Valuation
    forward_pe: float | None = None

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
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None

    # Shareholder returns
    eps: float | None = None
    dividend_yield: float | None = None

    # Company classification
    sector: str | None = None
    industry: str | None = None
