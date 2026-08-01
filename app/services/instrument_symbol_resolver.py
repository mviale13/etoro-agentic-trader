"""Resolve broker instrument identifiers into ticker symbols."""

from __future__ import annotations

from app.domain.watchlist_item import WatchlistItem
from app.services.watchlist_service import WatchlistService


class InstrumentSymbolResolver:
    """
    Map eToro instrument ids onto ticker symbols.

    The investor's watchlists are the available source of instrument
    metadata. A holding the watchlists do not describe keeps a visible
    placeholder identity rather than being dropped or renamed, so the
    portfolio stays complete and the gap stays obvious.
    """

    def __init__(
        self,
        watchlist_service: WatchlistService | None = None,
    ) -> None:
        self._watchlist_service = watchlist_service or WatchlistService()

    async def items(self) -> dict[int, WatchlistItem]:
        """Return every known instrument, keyed by instrument id."""

        watchlists = await self._watchlist_service.get()

        return {
            item.instrument_id: item
            for watchlist in watchlists
            for item in watchlist.items
        }

    @staticmethod
    def placeholder(instrument_id: int) -> str:
        """Identity used when the instrument cannot be named."""

        return f"#{instrument_id}"
