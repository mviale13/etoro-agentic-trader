"""The book's own earnings calendar: held and watched companies only."""

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.portfolio_position import PortfolioPosition
from app.domain.provenance import Provenance
from app.domain.watchlist_item import WatchlistItem
from app.infrastructure.cache.json_cache import JsonCache
from app.providers.earnings_provider import (
    CachedEarningsProvider,
    EarningsDatesProvider,
    ReadDates,
)
from app.services.earnings_calendar_service import EarningsCalendarService
from tests.test_brain_context import make_portfolio

#: The suite's "today" is the real one: the service partitions against
#: the current UTC date, and a pinned date would rot overnight.
TODAY = datetime.now(UTC).date()


def holding(symbol: str, instrument_id: int, asset_class: str) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=100.0,
        market_value_usd=100.0,
        unrealized_pnl_usd=0.0,
        asset_class=asset_class,
        instrument_id=instrument_id,
    )


def watched(instrument_id: int, symbol: str, asset_type_id: int = 5) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=f"{symbol} Company",
        asset_type_id=asset_type_id,
        asset_type_subcategory_id=0,
        exchange_id=0,
        rank=1,
        avatar_url=None,
    )


class PortfolioPerceptionStub:
    def __init__(self, holdings: tuple[PortfolioPosition, ...]) -> None:
        self._holdings = holdings

    async def execute(self):
        return replace(make_portfolio(), holdings=self._holdings)


class ResolverStub:
    def __init__(self, items: dict[int, WatchlistItem]) -> None:
        self._items = items

    async def items_for(self, instrument_ids):
        return self._items


class ProviderStub:
    """Canned dates per symbol; a symbol mapped to None fails to read."""

    def __init__(self, dates: dict[str, tuple[date, ...] | None]) -> None:
        self._dates = dates
        self.asked: list[str] = []

    def read(self, symbol: str) -> ReadDates:
        self.asked.append(symbol)
        dates = self._dates.get(symbol, ())

        if dates is None:
            raise RuntimeError("provider unreachable")

        return ReadDates(
            dates=dates,
            reading=Provenance(
                source="Yahoo Finance",
                observed_at=datetime(2026, 8, 5, 9, 0, tzinfo=UTC),
            ),
        )


def service(
    holdings: tuple[PortfolioPosition, ...],
    items: dict[int, WatchlistItem],
    dates: dict[str, tuple[date, ...] | None],
) -> tuple[EarningsCalendarService, ProviderStub]:
    provider = ProviderStub(dates)

    return (
        EarningsCalendarService(
            portfolio_perception=PortfolioPerceptionStub(holdings),  # type: ignore[arg-type]
            symbol_resolver=ResolverStub(items),  # type: ignore[arg-type]
            provider=provider,  # type: ignore[arg-type]
        ),
        provider,
    )


@pytest.mark.anyio
async def test_reports_are_sorted_soonest_first_with_held_stated() -> None:
    calendar_service, _ = service(
        holdings=(holding("DIS", 1016, "stock"),),
        items={
            1016: watched(1016, "DIS"),
            1003: watched(1003, "META"),
        },
        dates={
            "DIS": (TODAY,),
            "META": (TODAY + timedelta(days=84),),
        },
    )

    calendar = await calendar_service.upcoming()

    assert [entry.symbol for entry in calendar.upcoming] == ["DIS", "META"]

    disney, meta = calendar.upcoming

    assert disney.held is True
    assert disney.window.starts_on == TODAY
    assert disney.window.ends_on is None
    assert meta.held is False


@pytest.mark.anyio
async def test_only_companies_are_asked() -> None:
    """A token or a fund has no earnings call; asking would manufacture
    absences for instruments the question does not apply to."""

    calendar_service, provider = service(
        holdings=(
            holding("DIS", 1016, "stock"),
            holding("BTC", 100000, "crypto"),
        ),
        items={
            1016: watched(1016, "DIS"),
            100000: watched(100000, "BTC", asset_type_id=10),
            5555: watched(5555, "SPYY", asset_type_id=6),
        },
        dates={"DIS": (TODAY,)},
    )

    await calendar_service.upcoming()

    assert provider.asked == ["DIS"]


@pytest.mark.anyio
async def test_the_two_absences_stay_apart() -> None:
    """No published date is not the same fact as a failed read."""

    calendar_service, _ = service(
        holdings=(),
        items={
            1: watched(1, "AAAA"),
            2: watched(2, "BBBB"),
            3: watched(3, "CCCC"),
        },
        dates={
            "AAAA": (TODAY + timedelta(days=7),),
            "BBBB": (),
            "CCCC": None,
        },
    )

    calendar = await calendar_service.upcoming()

    assert [entry.symbol for entry in calendar.upcoming] == ["AAAA"]
    assert calendar.unscheduled == ("BBBB",)
    assert calendar.unread == ("CCCC",)


@pytest.mark.anyio
async def test_a_window_already_passed_is_filed_as_reported() -> None:
    """The provider keeps publishing the last window for a while after
    the report ran. It is the last report, not the next one, and it is
    never sorted ahead of the reports actually coming."""

    today = TODAY

    calendar_service, _ = service(
        holdings=(),
        items={
            1: watched(1, "PAST"),
            2: watched(2, "OLDER"),
            3: watched(3, "SOON"),
        },
        dates={
            "PAST": (today - timedelta(days=6),),
            "OLDER": (today - timedelta(days=8),),
            "SOON": (today + timedelta(days=2),),
        },
    )

    calendar = await calendar_service.upcoming()

    assert [entry.symbol for entry in calendar.upcoming] == ["SOON"]
    # Most recent first: the reader scans backwards from today.
    assert [entry.symbol for entry in calendar.reported] == ["PAST", "OLDER"]


@pytest.mark.anyio
async def test_a_window_keeps_both_of_its_ends() -> None:
    calendar_service, _ = service(
        holdings=(),
        items={1: watched(1, "AAAA")},
        dates={"AAAA": (TODAY + timedelta(days=3), TODAY + timedelta(days=7))},
    )

    calendar = await calendar_service.upcoming()

    assert calendar.upcoming[0].window.starts_on == TODAY + timedelta(days=3)
    assert calendar.upcoming[0].window.ends_on == TODAY + timedelta(days=7)


@pytest.mark.anyio
async def test_an_empty_book_is_an_empty_calendar() -> None:
    calendar_service, provider = service(holdings=(), items={}, dates={})

    calendar = await calendar_service.upcoming()

    assert calendar == await calendar_service.upcoming()
    assert provider.asked == []


# ------------------------------------------------------------------
# The daily cache: same calendar all day, stale served as last known.
# ------------------------------------------------------------------


class DatesStub(EarningsDatesProvider):
    def __init__(self, dates, fails: bool = False) -> None:
        self._dates = dates
        self._fails = fails
        self.calls = 0

    def dates(self, symbol: str):
        self.calls += 1

        if self._fails:
            raise RuntimeError("rate limited")

        return self._dates


def test_a_second_read_on_the_same_day_costs_nothing(tmp_path) -> None:
    stub = DatesStub((TODAY,))
    provider = CachedEarningsProvider(provider=stub, cache=JsonCache(tmp_path))

    first = provider.read("DIS")
    second = provider.read("DIS")

    assert stub.calls == 1
    assert second.dates == first.dates == (TODAY,)
    assert second.reading.last_known is False


def test_no_published_date_is_a_cached_answer_not_a_retry(tmp_path) -> None:
    stub = DatesStub(())
    provider = CachedEarningsProvider(provider=stub, cache=JsonCache(tmp_path))

    assert provider.read("DIS").dates == ()
    assert provider.read("DIS").dates == ()
    assert stub.calls == 1


def test_a_failed_read_serves_the_last_known_reading_marked(tmp_path) -> None:
    cache = JsonCache(tmp_path)

    CachedEarningsProvider(provider=DatesStub((TODAY,)), cache=cache).read("DIS")

    # Age the entry so it no longer reads as today's.
    entry_path = next(tmp_path.glob("*.json"))
    aged = entry_path.read_text().replace(str(TODAY.year), str(TODAY.year - 1))
    entry_path.write_text(aged)

    read = CachedEarningsProvider(
        provider=DatesStub((), fails=True),
        cache=cache,
    ).read("DIS")

    assert read.dates == (TODAY.replace(year=TODAY.year - 1),)
    assert read.reading.last_known is True


def test_a_failed_read_with_no_history_raises(tmp_path) -> None:
    provider = CachedEarningsProvider(
        provider=DatesStub((), fails=True),
        cache=JsonCache(tmp_path),
    )

    with pytest.raises(RuntimeError):
        provider.read("DIS")
