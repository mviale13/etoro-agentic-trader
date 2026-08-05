"""Describe instruments from the broker's own catalog."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, Protocol

from app.brokers.etoro_instruments import EtoroInstrumentsBroker
from app.config import Settings
from app.domain.provenance import Provenance
from app.domain.watchlist_item import WatchlistItem


class InstrumentsProvider(Protocol):
    async def fetch(self, instrument_ids: list[int]) -> dict[str, Any]: ...


class InstrumentMetadataService:
    """
    Turn the broker's catalog entries into instrument identities.

    Describing a held instrument from eToro's own catalog is a
    measurement, not a guess: the id being described is the id the
    broker reported the position under, and the symbol and type come
    back from the same source. An id the catalog does not return stays
    absent — the caller keeps its placeholder, and the gap stays
    visible rather than being filled with a lookalike.
    """

    #: The identity's source, named as the investor would see it.
    SOURCE = "eToro"

    def __init__(
        self,
        broker: InstrumentsProvider | None = None,
    ) -> None:
        self._broker = broker or EtoroInstrumentsBroker(Settings())

    async def describe(
        self,
        instrument_ids: Iterable[int],
    ) -> dict[int, WatchlistItem]:
        """The broker's description of each id it recognises, keyed by id."""

        wanted = sorted({int(instrument_id) for instrument_id in instrument_ids})

        if not wanted:
            return {}

        body = await self._broker.fetch(wanted)

        # The fetch is the observation of these identities; stamp the
        # moment it returned, exactly as the watchlist read does.
        reading = Provenance(source=self.SOURCE, observed_at=datetime.now(UTC))

        described: dict[int, WatchlistItem] = {}

        for entry in body.get("instrumentDisplayDatas") or ():
            item = self._item(entry, reading)

            if item is not None:
                described[item.instrument_id] = item

        return described

    @staticmethod
    def _item(
        entry: Any,
        reading: Provenance,
    ) -> WatchlistItem | None:
        """One catalog entry as an identity, or nothing where it cannot be."""

        if not isinstance(entry, dict):
            return None

        instrument_id = entry.get("instrumentID")
        symbol = entry.get("symbolFull")

        if not isinstance(instrument_id, int) or not isinstance(symbol, str):
            return None

        if not symbol.strip():
            return None

        name = entry.get("instrumentDisplayName")
        asset_type_id = entry.get("instrumentTypeID")
        exchange_id = entry.get("exchangeID")

        return WatchlistItem(
            instrument_id=instrument_id,
            symbol=symbol.strip(),
            name=name.strip() if isinstance(name, str) and name.strip() else symbol,
            # An unstated type id is 0, which classifies as UNKNOWN — the
            # honest reading of a catalog entry that did not say.
            asset_type_id=asset_type_id if isinstance(asset_type_id, int) else 0,
            asset_type_subcategory_id=0,
            exchange_id=exchange_id if isinstance(exchange_id, int) else 0,
            rank=0,
            avatar_url=None,
            reading=reading,
        )
