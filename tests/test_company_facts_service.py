"""What the platform knows about a company after one provider call."""

import asyncio
from datetime import UTC, datetime

from app.domain.company_facts import CompanyFacts
from app.domain.finding import statements
from app.domain.market_snapshot import MarketQuote
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.providers.yahoo_market_provider import YahooInstrument
from app.services.company_facts_service import CompanyFactsService
from app.services.quality_signal_service import QualitySignalService


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
        observed_at=observed_at,
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
    )

    return asyncio.run(service.build(item))


def test_company_facts_carry_everything_the_provider_returned() -> None:
    facts = make_facts(make_snapshot())

    assert facts.market_cap == 3_000_000_000_000.0
    assert facts.eps == 12.5
    assert facts.forward_pe == 21.5
    assert facts.dividend_yield == 0.012
    assert facts.current_price == 500.0


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


def build_crypto_facts() -> tuple[
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


def test_crypto_is_not_asked_for_company_fundamentals() -> None:
    """
    The provider answers about a token, and the answer reads like a company.

    A `marketCap` of 1.26 trillion, read as company facts, makes the quality
    signal report Bitcoin as a large-cap company. It has no company, so the
    fundamentals are reported absent rather than borrowed from a field that
    happens to be populated.
    """

    facts, _, valuation = build_crypto_facts()

    assert valuation.requested == []
    assert facts.market_cap is None

    signal = QualitySignalService().build(facts)

    assert signal.quality == "UNKNOWN"
    assert statements(signal.evidence) == ("Insufficient quality data.",)


def test_facts_carry_the_asset_class_rather_than_a_broker_id() -> None:
    facts, _, _ = build_crypto_facts()

    assert facts.asset_type == "crypto"
