from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.daily_change import DailyChange
from app.domain.earnings_schedule import EarningsSchedule
from app.domain.market_magnitude import MarketCapMagnitude
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

    #: Whose price this is, as the source that established it names the
    #: subject: `bitcoin`, `hyperliquid`, `bittensor`. Only a token
    #: carries one — an equity's price is identified by its ticker at a
    #: venue, and this is the crypto-native identifier a pair listing
    #: cannot supply. None everywhere else, and never a display name.
    price_identity: str | None = None

    #: Every source whose independent agreement established this price —
    #: the served claimant first, then the corroborators. Empty for a
    #: price that did not come from the crypto-native gate.
    #:
    #: A price served from a judged pool is not one provider's number,
    #: and naming only the served claimant would report it as one. The
    #: owner's ruling on #231 keeps the judged price *and* requires it
    #: to say who established it.
    price_claimants: tuple[str, ...] = ()

    #: The versioned rule that admitted this price. Empty where no rule
    #: did — a vendor quote read under its own ticker is not admitted by
    #: a gate, it is simply the vendor's figure.
    price_rule: str | None = None

    #: Why the data vendor's own listing for this symbol was not read as
    #: this security, where it was not.
    #:
    #: A refusal about the *vendor*, never a finding about the security:
    #: Yahoo's `HYPE-USD` is Supreme Finance, which says nothing about
    #: Hyperliquid. Carried so the refusal is observable rather than
    #: showing up only as three absent risk measurements.
    price_listing_refused: str | None = None

    daily_change_pct: float | None = None

    #: The same move, carrying what is established about it: whether it
    #: was measured at all, the warrant behind the translation, and
    #: which session it covers. Authoritative where the acquisition
    #: supplied one; `daily_change_pct` is the legacy float beside it,
    #: kept because twenty callers construct it directly and because a
    #: caller writing a bare number *is* asserting a measured change.
    #:
    #: The two never disagree on the live path — `CompanyFactsService`
    #: fills both from one quote — and a guard test asserts it.
    daily_change: "DailyChange | None" = None
    market_cap: float | None = None

    #: The same figure, carrying whether it may be compared with an
    #: absolute size threshold: the translation's warrant and whether
    #: the magnitude's denomination is established. Authoritative where
    #: the acquisition supplied one; `market_cap` above stays for every
    #: other reader and is filled from the same source.
    market_cap_magnitude: MarketCapMagnitude | None = None

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
    def price_provenance(self) -> str | None:
        """Who established this price, for what, when, and under which rule.

        The five things the owner's #231 ruling requires a judged crypto
        price to identify, in one sentence composed here so no surface
        assembles it differently: the token, the crypto-native provider's
        own identifier for it, the claimants whose independent agreement
        established the figure, the observation time, and the versioned
        rule that admitted it.

        None where the price was not admitted by a rule — an equity's
        quote is the vendor's own figure under the vendor's own ticker,
        and dressing it in this sentence would claim a corroboration
        nobody performed.
        """

        if self.price_rule is None or not self.price_claimants:
            return None

        established = (
            self.price_claimants[0]
            if len(self.price_claimants) == 1
            else (
                f"{', '.join(self.price_claimants[:-1])} and {self.price_claimants[-1]}"
            )
        )

        subject = (
            f"{self.symbol} ({self.price_identity})"
            if self.price_identity
            else self.symbol
        )

        observed = (
            "at an observation time the source did not state"
            if self.price_reading is None
            else (
                "observed "
                f"{self.price_reading.observed_at.astimezone(UTC):%Y-%m-%d %H:%M} UTC"
            )
        )

        return (
            f"The price for {subject} was established by {established}, "
            f"{observed}, under {self.price_rule}."
        )

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
