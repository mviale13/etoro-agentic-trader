"""The earnings calendar of the investor's own book."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.domain.asset_class import AssetClass
from app.domain.earnings_calendar import EarningsCalendar, EarningsDate
from app.providers.earnings_provider import CachedEarningsProvider
from app.services.instrument_symbol_resolver import InstrumentSymbolResolver


class EarningsCalendarService:
    """
    When the companies the investor holds or watches report next.

    Deliberately not the whole market's calendar. Thousands of companies
    report every week, and a list of them is context about everything
    and evidence about nothing. The companies whose reports can bear on
    this platform's decisions are the ones in the book — held or watched
    — so those are the ones whose dates are read, from the same provider
    the platform already trusts for their prices and fundamentals.

    Only companies are asked. A fund or a token has no earnings call,
    and asking would manufacture absences for instruments the question
    does not apply to.
    """

    def __init__(
        self,
        portfolio_perception: PortfolioPerception | None = None,
        symbol_resolver: InstrumentSymbolResolver | None = None,
        provider: CachedEarningsProvider | None = None,
    ) -> None:
        self._portfolio_perception = portfolio_perception or PortfolioPerception()
        self._symbol_resolver = symbol_resolver or InstrumentSymbolResolver()
        self._provider = provider or CachedEarningsProvider()

    async def upcoming(self) -> EarningsCalendar:
        companies = await self._companies()

        if not companies:
            return EarningsCalendar(upcoming=(), reported=(), unscheduled=(), unread=())

        symbols = sorted(companies)

        reads = await asyncio.gather(
            *(asyncio.to_thread(self._provider.read, symbol) for symbol in symbols),
            return_exceptions=True,
        )

        today = datetime.now(UTC).date()

        upcoming: list[EarningsDate] = []
        reported: list[EarningsDate] = []
        unscheduled: list[str] = []
        unread: list[str] = []

        for symbol, read in zip(symbols, reads, strict=True):
            if isinstance(read, BaseException):
                unread.append(symbol)
                continue

            window = read.window()

            if window is None:
                unscheduled.append(symbol)
                continue

            name, held = companies[symbol]

            entry = EarningsDate(
                symbol=symbol,
                name=name,
                held=held,
                window=window,
            )

            # The provider keeps publishing a window for a while after
            # the report ran. That is the last report, not the next one,
            # and it is filed as what it is.
            (upcoming if window.is_ahead_of(today) else reported).append(entry)

        upcoming.sort(key=lambda entry: (entry.window.starts_on, entry.symbol))
        reported.sort(key=lambda entry: (entry.window.starts_on, entry.symbol))
        reported.reverse()

        return EarningsCalendar(
            upcoming=tuple(upcoming),
            reported=tuple(reported),
            unscheduled=tuple(unscheduled),
            unread=tuple(unread),
        )

    async def _companies(self) -> dict[str, tuple[str, bool]]:
        """Every company in the book: symbol -> (name, held)."""

        portfolio = await self._portfolio_perception.execute()

        instruments = await self._symbol_resolver.items_for(
            tuple(holding.instrument_id for holding in portfolio.holdings)
        )

        companies: dict[str, tuple[str, bool]] = {}

        for holding in portfolio.holdings:
            if not holding.is_resolved:
                continue

            if holding.asset_class != AssetClass.STOCK.value:
                continue

            item = instruments.get(holding.instrument_id)

            companies[holding.symbol] = (
                item.name if item is not None and item.name else holding.symbol,
                True,
            )

        for item in instruments.values():
            if AssetClass.from_etoro(item.asset_type_id) is not AssetClass.STOCK:
                continue

            if not item.symbol or item.symbol in companies:
                continue

            companies[item.symbol] = (item.name or item.symbol, False)

        return companies
