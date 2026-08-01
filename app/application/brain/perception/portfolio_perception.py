"""Portfolio perception component for the MOVRvest investment brain."""

from collections.abc import Mapping
from dataclasses import replace

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.services.account_service import AccountService
from app.services.instrument_symbol_resolver import (
    InstrumentSymbolResolver,
)
from app.services.portfolio_service import PortfolioService


class PortfolioPerception:
    """Collect and interpret the investor's current portfolio."""

    def __init__(
        self,
        account_service: AccountService | None = None,
        portfolio_service: PortfolioService | None = None,
        symbol_resolver: InstrumentSymbolResolver | None = None,
    ) -> None:
        self._account_service = account_service or AccountService(
            EtoroAccountBroker(Settings())
        )
        self._portfolio_service = portfolio_service or PortfolioService()
        self._symbol_resolver = symbol_resolver or InstrumentSymbolResolver()

    async def execute(self) -> PortfolioSnapshot:
        """Build the current portfolio snapshot from broker account data."""
        account = await self._account_service.snapshot()

        snapshot = self._portfolio_service.analyze(account)

        return await self._resolve_symbols(snapshot)

    async def _resolve_symbols(
        self,
        snapshot: PortfolioSnapshot,
    ) -> PortfolioSnapshot:
        """Name each holding, so reasoning can work per security."""

        if not snapshot.holdings:
            return snapshot

        instruments = await self._symbol_resolver.items()

        holdings = tuple(
            replace(
                holding,
                symbol=self._symbol_for(holding.instrument_id, instruments),
            )
            if not holding.symbol
            else holding
            for holding in snapshot.holdings
        )

        largest = max(
            holdings,
            key=lambda holding: holding.market_value_usd,
            default=None,
        )

        return replace(
            snapshot,
            holdings=holdings,
            largest_position=largest.symbol if largest else None,
        )

    def _symbol_for(
        self,
        instrument_id: int,
        instruments: Mapping[int, WatchlistItem],
    ) -> str:
        item = instruments.get(instrument_id)

        symbol = item.symbol if item is not None else ""

        return symbol or self._symbol_resolver.placeholder(instrument_id)
