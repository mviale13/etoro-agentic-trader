"""Resolve broker instrument identifiers into ticker symbols."""

from __future__ import annotations

from collections.abc import Iterable

from app.domain.watchlist_item import WatchlistItem
from app.services.instrument_metadata_service import InstrumentMetadataService
from app.services.watchlist_service import WatchlistService


class InstrumentSymbolResolver:
    """
    Map eToro instrument ids onto ticker symbols.

    The investor's watchlists are the first source of instrument
    metadata. A holding the watchlists do not describe is asked about at
    the broker's own instrument catalog — the same source the position
    comes from — before anything is given up on. Only an instrument
    neither source can describe keeps a visible placeholder identity, so
    the portfolio stays complete and the gap stays obvious.
    """

    def __init__(
        self,
        watchlist_service: WatchlistService | None = None,
        metadata_service: InstrumentMetadataService | None = None,
    ) -> None:
        self._watchlist_service = watchlist_service or WatchlistService()
        self._metadata_service = metadata_service or InstrumentMetadataService()

    async def items(self) -> dict[int, WatchlistItem]:
        """Return every watched instrument, keyed by instrument id."""

        watchlists = await self._watchlist_service.get()

        return {
            item.instrument_id: item
            for watchlist in watchlists
            for item in watchlist.items
        }

    async def items_for(
        self,
        instrument_ids: Iterable[int],
    ) -> dict[int, WatchlistItem]:
        """
        Every watched instrument, plus the broker's description of the rest.

        `instrument_ids` are the ids the caller actually holds or needs.
        The ones no watchlist names are looked up in the broker's own
        catalog in one request; an id the catalog does not return stays
        out of the map, and the caller's placeholder path stands.
        """

        known = await self.items()

        missing = sorted(
            {int(instrument_id) for instrument_id in instrument_ids} - set(known)
        )

        if not missing:
            return known

        try:
            known.update(await self._metadata_service.describe(missing))
        except Exception:
            # The catalog being unreachable degrades to the watchlist-only
            # view: the holding keeps its placeholder and is reported as
            # unclassified — the same honest absence as before this
            # fallback existed, rather than a failed cycle.
            return known

        return known

    @staticmethod
    def placeholder(instrument_id: int) -> str:
        """Identity used when the instrument cannot be named."""

        return f"#{instrument_id}"
