"""Acquisition is a cycle an operator runs, never a page an investor opens.

Every surface serves what the store already holds and reaches no
provider. One dossier used to download a year of daily closes for each
holding and `SPY` thirteen times over — the benchmark is read once per
batch, and the page asked in batches of one — so opening a page was the
act that spent the rate limit and made the investor wait.

The cycle here is the other side of that rule: one batch, on purpose.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import pytest

from app.domain.asset_class import AssetClass
from app.domain.market_snapshot import MarketQuote
from app.domain.provenance import Provenance
from app.domain.research_candidate import ResearchCandidate
from app.domain.valuation_snapshot import ValuationSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.coingecko_market_provider import MarketClaimSet, MarketStateClaim
from app.providers.earnings_provider import ReadDates
from app.providers.yahoo_market_provider import YahooInstrument, YahooMarketProvider
from app.services.company_facts_service import CompanyFactsService
from app.services.market_acquisition_service import MarketAcquisitionService
from tests.test_brain_context import make_portfolio
from tests.test_cached_providers import CountingMarketProvider

# --- the read-only door ---------------------------------------------------


def instrument(symbol: str) -> YahooInstrument:
    return YahooInstrument(
        yahoo_symbol=symbol,
        movrvest_symbol=symbol,
        name=symbol,
    )


def age_entries_by(directory: Path, stored_at: datetime) -> None:
    """Make every stored entry look like it was written then, not now.

    `JsonCache` stamps the moment it wrote, and freshness is measured off
    that stamp — so an entry written now carrying an old reading is still
    a fresh entry. Both have to be old for the age to be the subject.
    """

    for path in directory.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["stored_at"] = stored_at.isoformat()

        path.write_text(json.dumps(record), encoding="utf-8")


def test_the_read_only_door_asks_no_provider_and_reports_the_absence(
    tmp_path: Path,
) -> None:
    """An empty store is an absence, not an error, and not a fetch."""

    provider = CountingMarketProvider()

    stored = CachedMarketProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=JsonCache(tmp_path),
        acquires=False,
    )

    assert asyncio.run(stored.quotes((instrument("MSFT"),))) == ()
    assert asyncio.run(stored.vix()) is None

    assert provider.requested == []


def test_a_stored_quote_is_served_with_the_moment_it_was_taken(
    tmp_path: Path,
) -> None:
    """
    Old evidence is still evidence when it carries its date.

    The acquiring door refuses a stale price and fetches, which is right
    for a cycle and is what made a page wait. The read-only door serves
    it dated — "Yahoo Finance, 3 hours ago" — which the surfaces already
    print verbatim.
    """

    taken = datetime.now(UTC) - timedelta(hours=3)
    cache = JsonCache(tmp_path)

    cache.write(
        "MSFT",
        {
            "symbol": "MSFT",
            "name": "Microsoft",
            "price": 400.0,
            "change_percent": 1.0,
            "currency": "USD",
            "source": "Yahoo Finance",
            "observed_at": taken.isoformat(),
        },
    )

    age_entries_by(tmp_path, taken)

    provider = CountingMarketProvider()

    quotes = asyncio.run(
        CachedMarketProvider(
            provider=provider,  # type: ignore[arg-type]
            cache=cache,
            acquires=False,
        ).quotes((instrument("MSFT"),))
    )

    assert len(quotes) == 1
    assert quotes[0].price == 400.0

    reading = quotes[0].reading
    assert reading is not None
    assert reading.observed_at == taken

    # Dated as it is, and never marked as a failure: nothing failed here,
    # because nothing was asked.
    assert reading.last_known is False
    assert reading.stated() == "Yahoo Finance, 3 hours ago"

    assert provider.requested == []

    # And the acquiring door, on the same store, does go and get it.
    asyncio.run(
        CachedMarketProvider(
            provider=provider,  # type: ignore[arg-type]
            cache=cache,
        ).quotes((instrument("MSFT"),))
    )

    assert provider.requested == ["MSFT"]


def test_stored_fundamentals_are_served_however_old_they_are(
    tmp_path: Path,
) -> None:
    """A company read some days ago is served as read some days ago."""

    cache = JsonCache(tmp_path)
    taken = datetime.now(UTC) - timedelta(days=4)

    CachedValueProvider(cache=cache)._cache.write(
        "MSFT",
        {
            "forward_pe": 30.0,
            "trailing_pe": None,
            "peg_ratio": None,
            "dividend_yield": None,
            "source": "Yahoo Finance",
            "observed_at": taken.isoformat(),
        },
    )

    snapshot = CachedValueProvider.stored(cache).snapshot("MSFT")

    assert snapshot.forward_pe == 30.0
    assert snapshot.reading is not None
    assert snapshot.reading.observed_at == taken


def test_fundamentals_never_read_are_absent_rather_than_estimated(
    tmp_path: Path,
) -> None:
    """Every figure absent, and undated — it was never read."""

    snapshot = CachedValueProvider.stored(JsonCache(tmp_path)).snapshot("MSFT")

    assert snapshot.forward_pe is None
    assert snapshot.market_cap is None
    assert snapshot.reading is None


def test_an_acquisition_that_fails_keeps_the_price_the_store_had(
    tmp_path: Path,
) -> None:
    """
    Walked into on the first real cycle, so it is pinned here.

    A holding that priced perfectly well failed once in a batch of
    twenty-two. The failure was written over its stored quote, and its
    page went from "Yahoo Finance, 3 hours ago" to no price at all — a
    provider hiccup deleting evidence this platform already had.
    """

    cache = JsonCache(tmp_path)
    taken = datetime.now(UTC) - timedelta(hours=3)

    cache.write(
        "DIS",
        {
            "symbol": "DIS",
            "name": "Walt Disney",
            "price": 95.0,
            "change_percent": -0.4,
            "currency": "USD",
            "source": "Yahoo Finance",
            "observed_at": taken.isoformat(),
        },
    )

    age_entries_by(tmp_path, taken)

    class FailingProvider:
        DEFAULT_INSTRUMENTS: tuple[YahooInstrument, ...] = ()

        async def quotes(
            self,
            instruments: tuple[YahooInstrument, ...] | None = None,
        ) -> tuple[MarketQuote, ...]:
            raise RuntimeError("Yahoo Finance did not answer")

        async def vix(self) -> float | None:
            return None

    # The acquiring door treats the stored quote as stale, tries, and
    # fails — which is a failed acquisition, and says so.
    with pytest.raises(RuntimeError):
        asyncio.run(
            CachedMarketProvider(
                provider=FailingProvider(),  # type: ignore[arg-type]
                cache=cache,
            ).quotes((instrument("DIS"),))
        )

    # And the surfaces still have the last real price, dated as what it is.
    served = asyncio.run(
        CachedMarketProvider.stored(cache).quotes((instrument("DIS"),))
    )

    assert len(served) == 1
    assert served[0].price == 95.0

    reading = served[0].reading
    assert reading is not None
    assert reading.observed_at == taken


def test_a_page_view_prices_nothing(tmp_path: Path) -> None:
    """
    The wiring this whole cycle exists for.

    `CompanyFactsService` runs once per security on every page view. Its
    three providers are the read-only doors, so opening a page cannot
    reach a provider whatever the store holds.
    """

    facts = CompanyFactsService()

    assert facts._market_provider._acquires is False  # type: ignore[union-attr]
    assert facts._valuation_provider._acquires is False  # type: ignore[union-attr]
    assert facts._earnings_provider._acquires is False  # type: ignore[union-attr]


# --- the cycle ------------------------------------------------------------


class BatchCountingProvider:
    """Reports how the caller batched its request, not just what it asked."""

    def __init__(self, unpriceable: tuple[str, ...] = ()) -> None:
        self.batches: list[tuple[str, ...]] = []
        self._unpriceable = unpriceable

    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        selected = instruments or ()

        self.batches.append(tuple(item.yahoo_symbol for item in selected))

        return tuple(
            MarketQuote(
                symbol=item.movrvest_symbol,
                name=item.name,
                price=100.0,
                change_percent=0.5,
                reading=Provenance(
                    source="Yahoo Finance",
                    observed_at=datetime.now(UTC),
                ),
            )
            for item in selected
            if item.movrvest_symbol not in self._unpriceable
        )

    async def vix(self) -> float | None:
        return 14.0


class ValuationStub:
    def __init__(self) -> None:
        self.asked: list[str] = []
        self.observed_with: list[tuple[str, object]] = []

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        self.asked.append(symbol)

        return ValuationSnapshot(
            forward_pe=20.0,
            trailing_pe=None,
            peg_ratio=None,
            dividend_yield=None,
            reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
        )

    def snapshot_observing(self, symbol: str, broker: object) -> ValuationSnapshot:
        """The observing door: same reading, and the broker claim arrives."""

        self.observed_with.append((symbol, broker))

        return self.snapshot(symbol)


class CalendarStub:
    def __init__(self) -> None:
        self.asked: list[str] = []

    def read(self, symbol: str) -> ReadDates:
        self.asked.append(symbol)

        return ReadDates(
            dates=(),
            reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
        )


class PortfolioStub:
    def __init__(self, holdings: tuple[Any, ...]) -> None:
        self._holdings = holdings

    async def execute(self) -> Any:
        return replace(make_portfolio(), holdings=self._holdings)


class OpportunityStub:
    def __init__(self, candidates: tuple[ResearchCandidate, ...]) -> None:
        self._candidates = candidates

    async def execute(self, portfolio: Any) -> tuple[ResearchCandidate, ...]:
        return self._candidates


class ResolverStub:
    def __init__(self, items: dict[int, WatchlistItem]) -> None:
        self._items = items

    async def items_for(self, instrument_ids: Any) -> dict[int, WatchlistItem]:
        return self._items


def watched(instrument_id: int, symbol: str) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=symbol,
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url=None,
    )


class HoldingStub:
    def __init__(self, instrument_id: int, symbol: str) -> None:
        self.instrument_id = instrument_id
        self.symbol = symbol
        self.is_resolved = True


def make_cycle(
    holdings: tuple[HoldingStub, ...],
    candidates: tuple[ResearchCandidate, ...] = (),
    quotes: BatchCountingProvider | None = None,
) -> tuple[MarketAcquisitionService, BatchCountingProvider]:
    provider = quotes or BatchCountingProvider()

    items = {
        holding.instrument_id: watched(holding.instrument_id, holding.symbol)
        for holding in holdings
    }
    items.update(
        {
            candidate.instrument_id: watched(candidate.instrument_id, candidate.symbol)
            for candidate in candidates
        }
    )

    service = MarketAcquisitionService(
        portfolio=PortfolioStub(holdings),
        opportunities=OpportunityStub(candidates),
        resolver=ResolverStub(items),
        quotes=provider,
        valuations=ValuationStub(),
        calendars=CalendarStub(),
        # The crypto market cycle runs on every acquisition rather than
        # only for a crypto security, so it is the one provider a book of
        # equities still reaches. Stubbed, or these tests would spend a
        # shared rate limit on eight live calls to measure batching.
        crypto_market=MarketCycleStub(),
    )

    return service, provider


class MarketCycleStub:
    """The crypto environment as a stub — read once per cycle, never fetched."""

    def __init__(self) -> None:
        self.cycles = 0

    def claims(
        self,
        coin_ids: tuple[str, ...] = (),
        category_keys: tuple[str, ...] = (),
    ) -> MarketClaimSet:
        self.cycles += 1

        return MarketClaimSet(
            source="CoinGecko",
            read=Provenance(source="CoinGecko", observed_at=datetime.now(UTC)),
            state=MarketStateClaim(total_market_cap=2_300_000_000_000.0),
        )


def candidate(instrument_id: int, symbol: str) -> ResearchCandidate:
    return ResearchCandidate(
        symbol=symbol,
        name=symbol,
        source="Watchlist",
        instrument_id=instrument_id,
        asset_class=AssetClass.STOCK.value,
    )


def test_the_whole_book_is_priced_in_one_batch() -> None:
    """
    The property the page path defeated, stated as a test.

    Sensitivity is measured against one benchmark and the provider reads
    that benchmark once per batch. A cycle asking in one batch pays for
    it once; a page asking security by security paid for it every time.
    """

    service, provider = make_cycle(
        holdings=(HoldingStub(1, "AAPL"), HoldingStub(2, "MSFT")),
        candidates=(candidate(3, "NVDA"),),
    )

    acquired = asyncio.run(service.acquire())

    assert len(provider.batches) == 1

    asked = provider.batches[0]

    assert {"AAPL", "MSFT", "NVDA"} <= set(asked)

    # The market strip travels in the same batch rather than a second one.
    assert "SPY" in asked

    # Asked for once each, however many surfaces would ask for them.
    assert len(asked) == len(set(asked))

    assert {security.symbol for security in acquired.priced} == {
        "AAPL",
        "MSFT",
        "NVDA",
    }


def test_a_security_that_could_not_be_priced_is_named() -> None:
    """The operator running the cycle is the only one who can act on it."""

    service, _ = make_cycle(
        holdings=(HoldingStub(1, "AAPL"), HoldingStub(2, "ETOR")),
        quotes=BatchCountingProvider(unpriceable=("ETOR",)),
    )

    acquired = asyncio.run(service.acquire())

    assert [security.symbol for security in acquired.unpriced] == ["ETOR"]


def test_the_candidate_budget_bounds_what_the_cycle_prices() -> None:
    """The research page's own number, so the page finds them priced."""

    service, provider = make_cycle(
        holdings=(HoldingStub(1, "AAPL"),),
        candidates=(
            candidate(2, "NVDA"),
            candidate(3, "AMD"),
            candidate(4, "INTC"),
        ),
    )

    asyncio.run(service.acquire(candidate_budget=2))

    asked = provider.batches[0]

    assert "NVDA" in asked
    assert "AMD" in asked
    assert "INTC" not in asked


def test_the_benchmark_is_downloaded_once_for_a_whole_batch(
    monkeypatch: Any,
) -> None:
    """
    Measured, then pinned.

    Thirteen `SPY` downloads for one dossier — 4.7 seconds of the 8.9
    spent downloading — because every security was its own batch. This
    is the provider's side of the same property.
    """

    downloads: list[str] = []

    days = pd.date_range("2025-01-01", periods=40, freq="D")

    def fake_download(yahoo_symbol: str) -> Any:
        downloads.append(yahoo_symbol)

        return pd.Series(
            [100.0 + index for index in range(len(days))],
            index=days,
        )

    monkeypatch.setattr(
        YahooMarketProvider,
        "_download_closes",
        staticmethod(fake_download),
    )

    asyncio.run(
        YahooMarketProvider().quotes(
            tuple(instrument(symbol) for symbol in ("AAPL", "MSFT", "NVDA"))
        )
    )

    assert downloads.count(YahooMarketProvider.BENCHMARK_SYMBOL) == 1


def test_book_and_candidate_fundamentals_go_through_the_observing_door() -> None:
    """The acquisition carries the broker claim to the funded read.

    Broker claims are never persisted, so the acquisition is the only
    layer that can hand one to the observation stream — a book or
    candidate security must be read through `snapshot_observing`, and
    the claim that arrives must be the broker's own account.
    """

    service, _ = make_cycle((HoldingStub(1, "AAPL"), HoldingStub(2, "KO")))
    valuations = service._valuations  # noqa: SLF001

    asyncio.run(service.acquire(candidate_budget=0))

    assert valuations.observed_with, "no funded read carried a broker claim"

    for _, broker in valuations.observed_with:
        assert broker.provider == "eToro"
        assert broker.symbol
        assert broker.taxonomy is not None, "the raw assetTypeId travels"

    # The stub's observing door delegates to its plain one, so `asked`
    # mirrors it; what matters is that every funded read arrived WITH a
    # broker claim — none reached the plain door directly.
    assert {symbol for symbol, _ in valuations.observed_with} == {"AAPL", "KO"}
    assert len(valuations.observed_with) == len(valuations.asked)
