"""What the platform knows about a company after one provider call."""

import asyncio
from datetime import UTC, datetime

from app.domain.company_facts import CompanyFacts
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
    assert "Insufficient quality data." not in signal.evidence


def test_facts_are_never_dated_fresher_than_the_evidence() -> None:
    observed_at = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)

    facts = make_facts(make_snapshot(observed_at=observed_at))

    assert facts.observed_at == observed_at
