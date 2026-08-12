from dataclasses import dataclass
from datetime import datetime

from app.domain.earnings_schedule import EarningsSchedule
from app.domain.market_sensitivity import MarketSensitivity
from app.domain.provenance import Provenance, oldest


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

    # Where each part of this came from, and when.
    #
    # One date used to cover the lot, and it was the fundamentals' date.
    # The price beside it could be fifteen minutes old and the identity
    # beside that came from a different service entirely — so the single
    # figure described one third of the object and dated the rest by
    # implication.

    #: The quote: price, day change, volatility, drawdown.
    price_reading: Provenance | None = None

    #: The fundamentals: valuation, size, earnings, supply.
    fundamentals_reading: Provenance | None = None

    #: The identity: symbol and name, read from the watchlist that named
    #: this instrument — a different source, on a different cadence, from
    #: the two above.
    identity_reading: Provenance | None = None

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

    #: How much this security moves with the market, measured against a
    #: benchmark rather than inferred from its asset class. None where the
    #: price history was too short, or the benchmark could not be read.
    market_sensitivity: MarketSensitivity | None = None

    #: When this company next reports, read from its own published
    #: calendar. None for anything that does not report — a fund, a token
    #: — which is never asked. A company that was asked always carries a
    #: schedule, even when it says nothing was published or nothing could
    #: be read: those two absences mean different things and are kept
    #: apart inside it.
    earnings: EarningsSchedule | None = None

    #: What a token has in place of company fundamentals. None for a
    #: company, which has a balance sheet instead.
    circulating_supply: float | None = None
    max_supply: float | None = None
    volume_24h: float | None = None
    inception: datetime | None = None

    #: What a fund has in place of company fundamentals: what owning it
    #: costs, as a decimal ratio of assets per year (0.0007 is 0.07%).
    #: None for anything that is not a fund. An evidenced fact about the
    #: wrapper — no score, band or verdict is ever derived from it.
    expense_ratio: float | None = None

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

    @property
    def observed_at(self) -> datetime | None:
        """
        The age this evidence can honestly claim: that of its stalest part.

        None when nothing here carries a reading at all, which is not the
        same as this being fresh.
        """

        reading = oldest(
            self.price_reading,
            self.fundamentals_reading,
            self.identity_reading,
        )

        return reading.observed_at if reading is not None else None
