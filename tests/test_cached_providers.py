"""Evidence that stays still while the day does."""

import asyncio
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.domain.market_sensitivity import MarketSensitivity
from app.domain.market_snapshot import MarketQuote
from app.domain.provenance import Provenance
from app.domain.valuation_snapshot import ValuationSnapshot
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.cached_value_provider import CachedValueProvider
from app.providers.yahoo_market_provider import YahooInstrument


class CountingValueProvider:
    """Reports how many times the provider was actually asked."""

    def __init__(self, snapshot: ValuationSnapshot | None = None) -> None:
        self.calls = 0
        self._snapshot = snapshot or ValuationSnapshot(
            forward_pe=21.5,
            trailing_pe=24.1,
            peg_ratio=1.4,
            dividend_yield=0.012,
            market_cap=3_000_000_000_000.0,
            eps=12.5,
            reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
        )

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        self.calls += 1

        return self._snapshot


class FailingValueProvider:
    def __init__(self) -> None:
        self.calls = 0

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        self.calls += 1

        raise RuntimeError("429 Too Many Requests")


def make_value_provider(
    tmp_path: Path,
    provider: object,
) -> CachedValueProvider:
    return CachedValueProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=JsonCache(tmp_path),
    )


def test_fundamentals_are_read_once_a_day(tmp_path: Path) -> None:
    provider = CountingValueProvider()
    cached = make_value_provider(tmp_path, provider)

    first = cached.snapshot("MSFT")
    second = cached.snapshot("MSFT")

    assert provider.calls == 1
    assert first == second


def test_a_replayed_reading_keeps_its_fundamentals(tmp_path: Path) -> None:
    """
    Growth, margins and cash flow survive the cache.

    Dropped on a same-day hit, they would leave the analysts nothing to
    analyse for the rest of the day the reading was taken.
    """

    snapshot = ValuationSnapshot(
        forward_pe=21.5,
        trailing_pe=24.1,
        peg_ratio=1.4,
        dividend_yield=0.012,
        market_cap=3_000_000_000_000.0,
        eps=12.5,
        gross_margin=0.48,
        revenue_growth=0.16,
        debt_to_equity=0.78,
        free_cash_flow=99_000_000_000.0,
        sector="Technology",
        reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
    )

    provider = CountingValueProvider(snapshot)
    cached = make_value_provider(tmp_path, provider)

    cached.snapshot("MSFT")
    replayed = cached.snapshot("MSFT")

    assert provider.calls == 1
    assert replayed.gross_margin == 0.48
    assert replayed.debt_to_equity == 0.78
    assert replayed.free_cash_flow == 99_000_000_000.0
    assert replayed.sector == "Technology"


def test_the_same_day_produces_the_same_evidence(tmp_path: Path) -> None:
    """A second run must not be able to change a decision on its own."""

    first = make_value_provider(tmp_path, CountingValueProvider()).snapshot("MSFT")

    moved = CountingValueProvider(
        ValuationSnapshot(
            forward_pe=99.0,
            trailing_pe=99.0,
            peg_ratio=9.9,
            dividend_yield=0.0,
            market_cap=1.0,
            eps=-5.0,
            reading=Provenance(source="Yahoo Finance", observed_at=datetime.now(UTC)),
        )
    )

    second = make_value_provider(tmp_path, moved).snapshot("MSFT")

    assert moved.calls == 0
    assert second.forward_pe == first.forward_pe
    assert second.eps == first.eps


def age_cache_by_a_day(tmp_path: Path) -> None:
    """Make every stored entry look like it was read yesterday."""

    yesterday = (datetime.now(UTC) - timedelta(days=1)).isoformat()

    for path in tmp_path.glob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        record["stored_at"] = yesterday
        record["value"]["observed_at"] = yesterday

        path.write_text(json.dumps(record), encoding="utf-8")


def test_a_failing_provider_serves_the_last_real_reading(tmp_path: Path) -> None:
    make_value_provider(tmp_path, CountingValueProvider()).snapshot("MSFT")

    age_cache_by_a_day(tmp_path)

    failing = FailingValueProvider()
    snapshot = CachedValueProvider(
        provider=failing,  # type: ignore[arg-type]
        cache=JsonCache(tmp_path),
    ).snapshot("MSFT")

    assert failing.calls == 1
    assert snapshot.forward_pe == 21.5

    # Old evidence is still evidence, but it is never dated today.
    assert snapshot.observed_at is not None
    assert snapshot.observed_at.date() < datetime.now(UTC).date()

    # And it is marked. Served under its own date alone it would be
    # indistinguishable from a reading taken on schedule, which hides a
    # provider outage behind a plausible-looking figure.
    assert snapshot.reading is not None
    assert snapshot.reading.last_known


def test_a_reading_served_on_its_normal_cadence_is_not_marked(
    tmp_path: Path,
) -> None:
    """Fundamentals are read once a day by design; that is not degradation."""

    provider = make_value_provider(tmp_path, CountingValueProvider())

    provider.snapshot("MSFT")
    snapshot = provider.snapshot("MSFT")

    assert snapshot.reading is not None
    assert not snapshot.reading.last_known


def test_a_failing_provider_with_nothing_remembered_still_fails(
    tmp_path: Path,
) -> None:
    with pytest.raises(RuntimeError):
        make_value_provider(tmp_path, FailingValueProvider()).snapshot("MSFT")


class CountingMarketProvider:
    DEFAULT_INSTRUMENTS = (
        YahooInstrument(
            yahoo_symbol="SPY",
            movrvest_symbol="SPY",
            name="S&P 500 ETF",
        ),
    )

    def __init__(self) -> None:
        self.requested: list[str] = []

    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        selected = instruments or self.DEFAULT_INSTRUMENTS

        self.requested.extend(instrument.yahoo_symbol for instrument in selected)

        return tuple(
            MarketQuote(
                symbol=instrument.movrvest_symbol,
                name=instrument.name,
                price=500.0,
                change_percent=1.5,
            )
            for instrument in selected
        )

    async def vix(self) -> float | None:
        return 14.0


def make_market_provider(
    tmp_path: Path,
    provider: CountingMarketProvider,
    ttl: timedelta = timedelta(minutes=15),
) -> CachedMarketProvider:
    return CachedMarketProvider(
        provider=provider,  # type: ignore[arg-type]
        cache=JsonCache(tmp_path),
        ttl=ttl,
    )


def make_instrument(symbol: str) -> YahooInstrument:
    return YahooInstrument(
        yahoo_symbol=symbol,
        movrvest_symbol=symbol,
        name=symbol,
    )


def test_a_recent_quote_is_not_requested_again(tmp_path: Path) -> None:
    provider = CountingMarketProvider()
    cached = make_market_provider(tmp_path, provider)
    instruments = (make_instrument("MSFT"),)

    asyncio.run(cached.quotes(instruments))
    asyncio.run(cached.quotes(instruments))

    assert provider.requested == ["MSFT"]


def test_only_the_missing_quotes_are_requested(tmp_path: Path) -> None:
    provider = CountingMarketProvider()
    cached = make_market_provider(tmp_path, provider)

    asyncio.run(cached.quotes((make_instrument("MSFT"),)))

    quotes = asyncio.run(
        cached.quotes(
            (
                make_instrument("MSFT"),
                make_instrument("NVDA"),
            )
        )
    )

    assert provider.requested == ["MSFT", "NVDA"]
    assert [quote.symbol for quote in quotes] == ["MSFT", "NVDA"]


def test_an_expired_quote_is_requested_again(tmp_path: Path) -> None:
    provider = CountingMarketProvider()
    instruments = (make_instrument("MSFT"),)

    asyncio.run(
        make_market_provider(tmp_path, provider, timedelta(0)).quotes(instruments)
    )
    asyncio.run(
        make_market_provider(tmp_path, provider, timedelta(0)).quotes(instruments)
    )

    # A price is a claim about now: once it expires it is fetched, never
    # replayed.
    assert provider.requested == ["MSFT", "MSFT"]


class PartiallyFailingMarketProvider(CountingMarketProvider):
    """Prices what it can; silent about the rest, like the real one."""

    async def quotes(
        self,
        instruments: tuple[YahooInstrument, ...] | None = None,
    ) -> tuple[MarketQuote, ...]:
        selected = instruments or self.DEFAULT_INSTRUMENTS

        self.requested.extend(instrument.yahoo_symbol for instrument in selected)

        return tuple(
            MarketQuote(
                symbol=instrument.movrvest_symbol,
                name=instrument.name,
                price=500.0,
                change_percent=1.5,
            )
            for instrument in selected
            if instrument.movrvest_symbol != "SOL"
        )


def test_an_unpriceable_symbol_costs_a_page_nothing_and_a_cycle_one_ask(
    tmp_path: Path,
) -> None:
    """
    Who is asking decides whether asking again is waste.

    A symbol that cannot be priced under its ticker — crypto without its
    `-USD` suffix, an eToro future with no Yahoo listing — was once
    remembered as unpriceable so it would not be re-asked. That memo
    existed because every page view fetched, and every page view then
    spent the rate limit the priceable securities needed.

    A page view no longer fetches at all, so the only caller left is an
    explicit acquisition — and one that skipped a security because it
    failed half an hour ago is refusing to do the one thing it was run
    for. So the cost is one ask per cycle, and the memo is gone with the
    behaviour that justified it.
    """

    provider = PartiallyFailingMarketProvider()
    instruments = (make_instrument("MSFT"), make_instrument("SOL"))

    cycle = make_market_provider(tmp_path, provider)

    first = asyncio.run(cycle.quotes(instruments))
    second = asyncio.run(cycle.quotes(instruments))

    assert [quote.symbol for quote in first] == ["MSFT"]
    assert [quote.symbol for quote in second] == ["MSFT"]

    # MSFT priced, so the second cycle serves it from the store. SOL did
    # not, so the second cycle asks about it again — once.
    assert provider.requested == ["MSFT", "SOL", "SOL"]

    # And a surface asks about neither, whatever the store holds.
    asyncio.run(CachedMarketProvider.stored(JsonCache(tmp_path)).quotes(instruments))

    assert provider.requested == ["MSFT", "SOL", "SOL"]


def test_the_market_index_is_read_once_too(tmp_path: Path) -> None:
    class CountingVix(CountingMarketProvider):
        def __init__(self) -> None:
            super().__init__()
            self.vix_calls = 0

        async def vix(self) -> float | None:
            self.vix_calls += 1
            return 14.0

    provider = CountingVix()
    cached = make_market_provider(tmp_path, provider)

    assert asyncio.run(cached.vix()) == 14.0
    assert asyncio.run(cached.vix()) == 14.0
    assert provider.vix_calls == 1


def test_a_replayed_quote_keeps_the_time_the_price_was_taken(tmp_path) -> None:
    """
    Otherwise a fifteen-minute-old price reports itself as current.

    The cache exists so the provider is not asked twice, and the whole
    value of that is undone if the copy it serves looks freshly fetched.
    """

    taken_at = datetime.now(UTC) - timedelta(minutes=14)

    class DatedProvider(CountingMarketProvider):
        async def quotes(
            self,
            instruments: tuple[YahooInstrument, ...] | None = None,
        ) -> tuple[MarketQuote, ...]:
            fetched = await super().quotes(instruments)

            return tuple(
                replace(
                    quote,
                    reading=Provenance(source="Yahoo Finance", observed_at=taken_at),
                )
                for quote in fetched
            )

    provider = CachedMarketProvider(
        provider=DatedProvider(),  # type: ignore[arg-type]
        cache=JsonCache(str(tmp_path)),
    )

    live = asyncio.run(provider.quotes())
    replayed = asyncio.run(provider.quotes())

    assert live[0].reading is not None
    assert replayed[0].reading is not None
    assert replayed[0].reading.observed_at == taken_at
    assert replayed[0].reading.source == "Yahoo Finance"


def test_a_replayed_quote_keeps_its_measured_market_sensitivity(tmp_path) -> None:
    """
    Sensitivity is measured off a year of history the cache never holds.

    A replayed quote cannot recompute it — the benchmark series it was
    regressed on is long gone — so dropping it on a cache hit would make a
    beta blink out fifteen minutes after every fetch.
    """

    measured = MarketSensitivity(
        beta=1.35,
        correlation=0.68,
        observations=240,
        benchmark="SPY",
    )

    class SensitiveProvider(CountingMarketProvider):
        async def quotes(
            self,
            instruments: tuple[YahooInstrument, ...] | None = None,
        ) -> tuple[MarketQuote, ...]:
            fetched = await super().quotes(instruments)

            return tuple(
                replace(quote, market_sensitivity=measured) for quote in fetched
            )

    provider = CachedMarketProvider(
        provider=SensitiveProvider(),  # type: ignore[arg-type]
        cache=JsonCache(str(tmp_path)),
    )

    asyncio.run(provider.quotes())
    replayed = asyncio.run(provider.quotes())

    assert replayed[0].market_sensitivity == measured


class RefusingValueProvider:
    """Answers the way `Ticker.info` does when the provider refuses.

    Not with an exception — with a payload carrying nothing, which read
    literally is a completed reading in which every figure is absent.
    """

    def __init__(self) -> None:
        self.calls = 0

    def snapshot(self, symbol: str) -> ValuationSnapshot:
        self.calls += 1

        return ValuationSnapshot(
            forward_pe=None,
            trailing_pe=None,
            peg_ratio=None,
            dividend_yield=None,
        )


def test_a_refusal_is_never_cached_as_a_reading(tmp_path: Path) -> None:
    """
    McDonald's spent a day reported as a company nobody had measured.

    One rate-limited call returned a payload with nothing in it. Stored
    as a reading, `is_from_today` then refused to read the company again
    until midnight, and every figure downstream was unknown — while
    Yahoo had 181 fields for MCD the whole time.
    """

    real = CountingValueProvider()

    # The refusal is stored the way it used to be, before the provider
    # raised on one.
    cache = JsonCache(tmp_path)
    cache.write(
        "MCD",
        {"forward_pe": None, "source": "Yahoo Finance", "observed_at": None},
    )

    snapshot = CachedValueProvider(
        provider=real,  # type: ignore[arg-type]
        cache=cache,
    ).snapshot("MCD")

    # Read again rather than served, though the entry is from today.
    assert real.calls == 1
    assert snapshot.forward_pe is not None


def test_a_stored_refusal_is_not_served_as_evidence(tmp_path: Path) -> None:
    """The read-only door reports it unread rather than as measured."""

    cache = JsonCache(tmp_path)
    cache.write(
        "MCD",
        {"forward_pe": None, "source": "Yahoo Finance", "observed_at": None},
    )

    snapshot = CachedValueProvider.stored(cache).snapshot("MCD")

    assert snapshot.carries_nothing
    assert snapshot.reading is None
