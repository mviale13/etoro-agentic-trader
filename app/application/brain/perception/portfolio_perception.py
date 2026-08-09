"""Portfolio perception component for the MOVRvest investment brain."""

import logging
from collections.abc import Mapping
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.domain.asset_class import AssetClass
from app.domain.portfolio_drawdown import PortfolioDrawdown
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.services.account_service import AccountService
from app.services.instrument_symbol_resolver import (
    InstrumentSymbolResolver,
)
from app.services.portfolio_drawdown_service import PortfolioDrawdownService
from app.services.portfolio_history_service import PortfolioHistoryService
from app.services.portfolio_service import PortfolioService

logger = logging.getLogger(__name__)


class PortfolioPerception:
    """Collect and interpret the investor's current portfolio."""

    def __init__(
        self,
        account_service: AccountService | None = None,
        portfolio_service: PortfolioService | None = None,
        symbol_resolver: InstrumentSymbolResolver | None = None,
        history_service: PortfolioHistoryService | None = None,
        drawdown_service: PortfolioDrawdownService | None = None,
    ) -> None:
        self._account_service = account_service or AccountService(
            EtoroAccountBroker(Settings())
        )
        self._portfolio_service = portfolio_service or PortfolioService()
        self._symbol_resolver = symbol_resolver or InstrumentSymbolResolver()
        self._history_service = history_service or PortfolioHistoryService()
        self._drawdown_service = drawdown_service or PortfolioDrawdownService()

    async def execute(self) -> PortfolioSnapshot:
        """Build the current portfolio snapshot from broker account data."""
        account = await self._account_service.snapshot()

        snapshot = self._portfolio_service.analyze(account)

        snapshot = await self._resolve_symbols(snapshot)

        drawdown = await self._drawdown()

        if drawdown is None:
            return snapshot

        return replace(snapshot, drawdown=drawdown)

    async def _drawdown(self) -> PortfolioDrawdown | None:
        """
        What the account has been through, or nothing.

        One extra request per cycle against a pooled allowance, for the
        only evidence here that describes more than this morning.

        A failure costs the drawdown, not the cycle. The account snapshot
        is what the platform cannot reason without; the history is what it
        would like to have, and an unreachable history is reported as
        unmeasured — which is exactly what it is.
        """

        since = (
            datetime.now(UTC) - timedelta(days=PortfolioHistoryService.WINDOW_DAYS)
        ).date()

        try:
            curve = await self._history_service.equity_curve(since)
        except Exception:
            logger.warning(
                "Balance history was unreachable; portfolio drawdown is unmeasured.",
                exc_info=True,
            )

            return None

        return self._drawdown_service.measure(curve)

    async def _resolve_symbols(
        self,
        snapshot: PortfolioSnapshot,
    ) -> PortfolioSnapshot:
        """
        Name each holding and say what kind of thing it is.

        The watchlists are the only description the platform has of an
        instrument, and they already carry its eToro asset type. The join
        was never made, so every holding stayed unclassified and the
        policy's stock, ETF and crypto targets had nothing to measure
        against.
        """

        if not snapshot.holdings:
            return snapshot

        instruments = await self._symbol_resolver.items_for(
            tuple(holding.instrument_id for holding in snapshot.holdings)
        )

        holdings = tuple(
            replace(
                holding,
                symbol=(
                    holding.symbol
                    or self._symbol_for(holding.instrument_id, instruments)
                ),
                asset_class=self._asset_class_for(
                    holding.instrument_id,
                    instruments,
                ),
            )
            for holding in snapshot.holdings
        )

        # The largest holding is named by `allocate`, which sums by
        # instrument as the policy does. Naming it here was a second
        # implementation of the same question, and it answered by row —
        # so it named the biggest single trade while the percentage
        # beside it measured something else.
        return self._portfolio_service.allocate(replace(snapshot, holdings=holdings))

    @staticmethod
    def _asset_class_for(
        instrument_id: int,
        instruments: Mapping[int, WatchlistItem],
    ) -> str | None:
        """
        What kind of asset this holding is, or nothing.

        A holding no watchlist describes cannot be classified. It stays
        unclassified and is reported as such rather than being counted into
        whichever bucket happens to be largest.
        """

        item = instruments.get(instrument_id)

        if item is None:
            return None

        return AssetClass.from_etoro(item.asset_type_id).value

    def _symbol_for(
        self,
        instrument_id: int,
        instruments: Mapping[int, WatchlistItem],
    ) -> str:
        item = instruments.get(instrument_id)

        symbol = item.symbol if item is not None else ""

        return symbol or self._symbol_resolver.placeholder(instrument_id)
