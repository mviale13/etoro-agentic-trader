"""What the platform knows about a company after one provider call."""

import asyncio
from datetime import UTC, date, datetime, timedelta

from app.domain.company_facts import CompanyFacts
from app.domain.finding import statements
from app.domain.market_snapshot import MarketQuote
from app.domain.provenance import Provenance
from app.domain.token_fact_validation import TokenClaimSet
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.providers.earnings_provider import ReadDates
from app.providers.yahoo_market_provider import YahooInstrument
from app.services.company_facts_service import CompanyFactsService
from app.services.quality_signal_service import QualitySignalService
from app.services.token_facts_service import TokenFactsService

#: The suite's "today" is the real one: the facts are read against the
#: current UTC date, and a pinned date would rot overnight.
TODAY = datetime.now(UTC).date()


class StubEarningsProvider:
    """
    A canned calendar read, remembering who it was asked about.

    `dates=None` is a provider that cannot be reached, which is a different
    answer from a company with no date published and is tested as one.
    """

    def __init__(self, dates: tuple[date, ...] | None = ()) -> None:
        self._dates = dates
        self.asked: list[str] = []

    def read(self, symbol: str) -> ReadDates:
        self.asked.append(symbol)

        if self._dates is None:
            raise RuntimeError("provider unreachable")

        return ReadDates(
            dates=self._dates,
            reading=Provenance(
                source="Yahoo Finance",
                observed_at=datetime.now(UTC),
            ),
        )


class StubMarketProvider:
    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        return (
            MarketQuote(
                symbol="MSFT",
                name="Microsoft",
                price=500.0,
                change_percent=1.5,
            ),
        )


class StubValuationProvider:
    def __init__(self, snapshot: ValuationSnapshot) -> None:
        self._snapshot = snapshot

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        return self._snapshot


def make_snapshot(
    observed_at: datetime | None = None,
) -> ValuationSnapshot:
    return ValuationSnapshot(
        forward_pe=21.5,
        trailing_pe=24.1,
        peg_ratio=1.4,
        dividend_yield=0.012,
        market_cap=3_000_000_000_000.0,
        eps=12.5,
        reading=(
            Provenance(source="Yahoo Finance", observed_at=observed_at)
            if observed_at is not None
            else None
        ),
    )


def make_facts(snapshot: ValuationSnapshot) -> CompanyFacts:
    item = WatchlistItem(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )

    service = CompanyFactsService(
        market_provider=StubMarketProvider(),  # type: ignore[arg-type]
        valuation_provider=StubValuationProvider(snapshot),  # type: ignore[arg-type]
        earnings_provider=StubEarningsProvider(),  # type: ignore[arg-type]
    )

    return asyncio.run(service.build(item))


def test_company_facts_carry_everything_the_provider_returned() -> None:
    facts = make_facts(make_snapshot())

    assert facts.market_cap == 3_000_000_000_000.0
    assert facts.eps == 12.5
    assert facts.forward_pe == 21.5
    assert facts.dividend_yield == 0.012
    assert facts.current_price == 500.0


def test_company_facts_carry_the_fundamentals_for_a_company() -> None:
    """Growth, margins and cash flow reach the facts, not just valuation."""

    snapshot = ValuationSnapshot(
        forward_pe=None,
        trailing_pe=None,
        peg_ratio=None,
        dividend_yield=None,
        gross_margin=0.48,
        operating_margin=0.31,
        net_margin=0.24,
        revenue_growth=0.16,
        debt_to_equity=0.78,
        current_ratio=1.07,
        free_cash_flow=99_000_000_000.0,
        return_on_equity=1.5,
        sector="Technology",
    )

    facts = make_facts(snapshot)

    assert facts.gross_margin == 0.48
    assert facts.revenue_growth == 0.16
    assert facts.debt_to_equity == 0.78
    assert facts.free_cash_flow == 99_000_000_000.0
    assert facts.roe == 1.5
    assert facts.sector == "Technology"


def test_quality_can_be_assessed_from_those_facts() -> None:
    """
    The quality signal needs size, earnings and dividends.

    While company facts discarded market cap and earnings, the signal could
    never score above LOW whatever the provider returned, and the Artificial
    CIO scored those companies on portfolio health instead.
    """

    signal = QualitySignalService().build(make_facts(make_snapshot()))

    assert signal.quality == "HIGH"
    assert "Insufficient quality data." not in statements(signal.evidence)


def test_facts_are_never_dated_fresher_than_the_evidence() -> None:
    observed_at = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)

    facts = make_facts(make_snapshot(observed_at=observed_at))

    assert facts.observed_at == observed_at


def test_identity_reading_is_carried_from_the_watchlist_item() -> None:
    """The symbol and name are dated by the fetch that named them."""

    identity = Provenance(
        source="eToro",
        observed_at=datetime(2026, 8, 4, 9, 30, tzinfo=UTC),
    )
    item = WatchlistItem(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
        reading=identity,
    )

    service = CompanyFactsService(
        market_provider=StubMarketProvider(),  # type: ignore[arg-type]
        valuation_provider=StubValuationProvider(make_snapshot()),  # type: ignore[arg-type]
        earnings_provider=StubEarningsProvider(),  # type: ignore[arg-type]
    )

    facts = asyncio.run(service.build(item))

    assert facts.identity_reading is identity


def test_a_stale_identity_ages_the_whole_object() -> None:
    """
    A last-known identity is part of the evidence, and dates it.

    The object can only honestly claim the age of its stalest part, and once
    the watchlist is running on memory that part can be the identity.
    """

    stale_identity = Provenance(
        source="eToro",
        observed_at=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
        last_known=True,
    )
    item = WatchlistItem(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
        reading=stale_identity,
    )

    service = CompanyFactsService(
        market_provider=StubMarketProvider(),  # type: ignore[arg-type]
        valuation_provider=StubValuationProvider(  # type: ignore[arg-type]
            make_snapshot(observed_at=datetime(2026, 8, 4, 9, 0, tzinfo=UTC)),
        ),
        earnings_provider=StubEarningsProvider(),  # type: ignore[arg-type]
    )

    facts = asyncio.run(service.build(item))

    assert facts.observed_at == stale_identity.observed_at


class RecordingMarketProvider:
    """A provider that remembers which ticker it was asked about."""

    def __init__(self, quote: MarketQuote) -> None:
        self.requested: list[str] = []
        self._quote = quote

    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        self.requested.extend(
            instrument.yahoo_symbol for instrument in instruments or ()
        )

        return (self._quote,)


class RecordingValuationProvider:
    def __init__(self) -> None:
        self.requested: list[str] = []

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        self.requested.append(symbol)

        # What Yahoo actually answers for BTC-USD: a network's total value,
        # in the field a business reports its equity value under.
        return ValuationSnapshot(
            forward_pe=None,
            trailing_pe=None,
            peg_ratio=None,
            dividend_yield=None,
            market_cap=1_255_684_964_352.0,
            circulating_supply=20_065_192.0,
            max_supply=21_000_000.0,
            volume_24h=19_753_431_040.0,
            inception=datetime(2010, 7, 13, tzinfo=UTC),
        )


BITCOIN = WatchlistItem(
    instrument_id=100000,
    symbol="BTC",
    name="Bitcoin",
    asset_type_id=10,
    asset_type_subcategory_id=1001,
    exchange_id=8,
    rank=0,
    avatar_url=None,
)


class StubClaimSource:
    """One pool claimant, offline."""

    def __init__(self, claims: TokenClaimSet | None) -> None:
        self._claims = claims

    def claim_set(self, symbol: str) -> TokenClaimSet | None:
        return self._claims


BTC_MARKET_CAP = 1_255_684_964_352.0
BTC_CIRCULATING = 20_065_192.0
BTC_PRICE = BTC_MARKET_CAP / BTC_CIRCULATING


def bitcoin_claims(source: str, **overrides: object) -> TokenClaimSet:
    """BTC as one claimant reports it, arithmetic intact."""

    values: dict[str, object] = {
        "source": source,
        "read": Provenance(
            source=source,
            observed_at=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
        ),
        "symbol_echo": "BTC",
        "price": BTC_PRICE,
        "market_cap": BTC_MARKET_CAP,
        "circulating_supply": BTC_CIRCULATING,
        "max_supply": 21_000_000.0,
        "fully_diluted_valuation": BTC_PRICE * 21_000_000.0,
    }

    values.update(overrides)

    return TokenClaimSet(**values)  # type: ignore[arg-type]


def bitcoin_pool() -> tuple[StubClaimSource, ...]:
    """Two independent claimants agreeing, plus the generalist's voice.

    Independent corroboration is what establishment now requires —
    agreement inside one provider is not corroboration — and the
    generalist's matching market-cap claim is what opens the volume
    gate.
    """

    native = bitcoin_claims(
        "TokenInsight",
        provider_id="bitcoin",
        rank=1.0,
        spot_volume_24h=3_657_000_000.0,
        spot_volume_change_24h=0.5,
        price_change_24h=0.006,
    )

    corroborator = bitcoin_claims("CoinGecko", provider_id="bitcoin")

    generalist = TokenClaimSet(
        source="Yahoo Finance",
        read=Provenance(
            source="Yahoo Finance",
            observed_at=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
        ),
        market_cap=BTC_MARKET_CAP,
        circulating_supply=BTC_CIRCULATING,
    )

    return (
        StubClaimSource(native),
        StubClaimSource(corroborator),
        StubClaimSource(generalist),
    )


def build_crypto_facts(
    earnings: StubEarningsProvider | None = None,
    sources: tuple[StubClaimSource, ...] | None = None,
) -> tuple[
    CompanyFacts,
    RecordingMarketProvider,
    RecordingValuationProvider,
]:
    market = RecordingMarketProvider(
        MarketQuote(
            symbol="BTC",
            name="Bitcoin",
            price=62_537.75,
            change_percent=-0.8,
            realized_volatility=0.47,
            max_drawdown=0.31,
        )
    )

    valuation = RecordingValuationProvider()

    service = CompanyFactsService(
        market_provider=market,  # type: ignore[arg-type]
        valuation_provider=valuation,  # type: ignore[arg-type]
        earnings_provider=earnings or StubEarningsProvider(),  # type: ignore[arg-type]
        token_facts=TokenFactsService(
            sources=sources if sources is not None else bitcoin_pool(),
        ),
    )

    return asyncio.run(service.build(BITCOIN)), market, valuation


def test_crypto_is_priced_under_the_ticker_that_resolves() -> None:
    """
    `BTC` returns nothing from Yahoo; `BTC-USD` returns a year of prices.

    Every crypto holding and candidate was therefore unpriceable, and since
    absent evidence stops an investment case at INVESTIGATE, none of them
    could ever progress.
    """

    _, market, _ = build_crypto_facts()

    assert market.requested == ["BTC-USD"]


def test_crypto_evidence_comes_back_under_its_own_symbol() -> None:
    facts, _, _ = build_crypto_facts()

    assert facts.symbol == "BTC"
    assert facts.current_price == 62_537.75
    assert facts.realized_volatility == 0.47
    assert facts.max_drawdown == 0.31


def test_a_tokens_market_cap_is_never_read_as_company_quality() -> None:
    """
    The provider answers about a token, and the answer reads like a company.

    A `marketCap` of 1.26 trillion is a network's total value, reported in
    the field a business reports its equity value under. Fed to the company
    quality signal it makes Bitcoin a large-cap company, which is why that
    signal is not the one a token is sent to.
    """

    facts, _, _ = build_crypto_facts()

    # The hazard, demonstrated: asked the company question, a token
    # answers as a company.
    mistaken = QualitySignalService().build(facts)

    assert "Large-cap company." in statements(mistaken.evidence)

    # The path a token actually takes asks it about itself.
    from app.services.crypto_quality_signal_service import (
        CryptoQualitySignalService,
    )

    signal = CryptoQualitySignalService().build(facts)

    assert "Large-cap company." not in statements(signal.evidence)
    assert any("market value" in line for line in statements(signal.evidence))


def test_a_token_carries_what_the_gate_established() -> None:
    """Supply and turnover — served from validated facts, not responses.

    The market value and supply are the gate's established figures. The
    generalist's broader volume flows because its own market-cap claim
    was independently corroborated — the sibling-authority rule.
    """

    facts, _, _ = build_crypto_facts()

    assert facts.market_cap == 1_255_684_964_352.0
    assert facts.circulating_supply == 20_065_192.0
    assert facts.max_supply == 21_000_000.0
    assert facts.volume_24h == 19_753_431_040.0


def test_a_tokens_age_is_never_a_provider_inception_field() -> None:
    """The bad-age regression: HYPE claimed six years it never traded.

    The generalist's inception field claimed 2020 for a token that began
    trading in 2024, and the age factor scored the fabrication as
    favourable. What that field measures for a token was never
    established, so a cryptocurrency's inception is never read from it —
    even where, as with Bitcoin's 2010, it happens to look right.
    """

    facts, _, _ = build_crypto_facts()

    assert facts.inception is None

    # And therefore no quality factor can say "Traded for N years".
    from app.services.crypto_quality_signal_service import (
        CryptoQualitySignalService,
    )

    signal = CryptoQualitySignalService().build(facts)

    assert not any("Traded for" in line for line in statements(signal.evidence))


def test_a_conflicted_market_value_never_leaks_as_established() -> None:
    """The S1 regression, at the assembly.

    Two coherent claimants disagreeing materially — the HYPE shape —
    leave the market value CONFLICTED. The assembly serves None, never
    one side of the argument, and the volume gate stays shut with it:
    a conflicted market value corroborates nobody.
    """

    def hype_shaped(
        source: str, market_cap: float, circulating: float
    ) -> TokenClaimSet:
        price = market_cap / circulating

        return TokenClaimSet(
            source=source,
            read=Provenance(
                source=source,
                observed_at=datetime(2026, 8, 10, 8, 0, tzinfo=UTC),
            ),
            symbol_echo="BTC",  # the fixture's instrument, HYPE's shape
            price=price,
            market_cap=market_cap,
            circulating_supply=circulating,
            max_supply=1_000_000_000.0,
            fully_diluted_valuation=price * 1_000_000_000.0,
        )

    facts, _, _ = build_crypto_facts(
        sources=(
            StubClaimSource(
                hype_shaped("TokenInsight", 18_260_000_000.0, 336_685_219.0)
            ),
            StubClaimSource(hype_shaped("CoinGecko", 12_150_000_000.0, 222_445_714.0)),
        ),
    )

    # Neither claimant's figure is served: the conflict does not leak.
    assert facts.market_cap is None
    assert facts.circulating_supply is None

    # And no volume: nothing corroborated the generalist's claim.
    assert facts.volume_24h is None


def test_a_single_claimant_cannot_establish_the_assembly_inputs() -> None:
    """Agreement inside one provider is not corroboration.

    A lone coherent claimant — the stale-ARB shape — yields claims,
    and the assembly consumes established values only: every token
    field reads absent, which is the honest state of single-source
    knowledge.
    """

    facts, _, _ = build_crypto_facts(
        sources=(
            StubClaimSource(bitcoin_claims("TokenInsight", provider_id="bitcoin")),
        ),
    )

    assert facts.market_cap is None
    assert facts.circulating_supply is None
    assert facts.max_supply is None
    assert facts.volume_24h is None


def test_a_token_carries_no_company_fundamentals() -> None:
    """No earnings, no dividend, no price/earnings ratio — never borrowed."""

    facts, _, _ = build_crypto_facts()

    assert facts.eps is None
    assert facts.dividend_yield is None
    assert facts.forward_pe is None


def test_facts_carry_the_asset_class_rather_than_a_broker_id() -> None:
    facts, _, _ = build_crypto_facts()

    assert facts.asset_type == "crypto"


# ── When the company next reports ───────────────────────────────────


def company_facts(
    earnings: StubEarningsProvider,
) -> CompanyFacts:
    item = WatchlistItem(
        instrument_id=1,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )

    service = CompanyFactsService(
        market_provider=StubMarketProvider(),  # type: ignore[arg-type]
        valuation_provider=StubValuationProvider(make_snapshot()),  # type: ignore[arg-type]
        earnings_provider=earnings,  # type: ignore[arg-type]
    )

    return asyncio.run(service.build(item))


def test_a_companys_published_report_window_reaches_its_facts() -> None:
    """The date the case's catalyst is built from, read once, per company."""

    report_day = TODAY + timedelta(days=6)

    facts = company_facts(StubEarningsProvider(dates=(report_day,)))

    assert facts.earnings is not None
    assert facts.earnings.unread is False
    assert facts.earnings.window is not None
    assert facts.earnings.window.starts_on == report_day
    assert facts.earnings.window.ends_on is None


def test_a_company_with_no_date_published_says_so_rather_than_nothing() -> None:
    """
    Asked, and the answer was that nothing is scheduled.

    A schedule is still present: the company was asked and it answered. It
    is the window inside it that is absent, which is what stops "no report
    is scheduled" being confused with "nobody looked".
    """

    facts = company_facts(StubEarningsProvider(dates=()))

    assert facts.earnings is not None
    assert facts.earnings.window is None
    assert facts.earnings.unread is False


def test_a_calendar_that_could_not_be_read_is_never_a_quiet_quarter() -> None:
    """A provider failure is stated as one, not as an absence of news."""

    facts = company_facts(StubEarningsProvider(dates=None))

    assert facts.earnings is not None
    assert facts.earnings.unread is True
    assert facts.earnings.window is None


def test_a_token_is_never_asked_when_it_next_reports() -> None:
    """
    A cryptocurrency has no earnings call, so the question is not put.

    Asking would manufacture an absence for an instrument the question was
    never valid for — and an absence on a dashboard reads as a finding.
    """

    earnings = StubEarningsProvider(dates=(TODAY,))

    facts, _, _ = build_crypto_facts(earnings)

    assert earnings.asked == []
    assert facts.earnings is None
