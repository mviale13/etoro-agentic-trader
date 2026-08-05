"""The broker's catalog describes held instruments no watchlist names."""

import pytest

from app.domain.watchlist_item import WatchlistItem
from app.services.instrument_metadata_service import InstrumentMetadataService
from app.services.instrument_symbol_resolver import InstrumentSymbolResolver

#: The catalog entry for eToro instrument 1238, as the live endpoint
#: returned it (trimmed to the fields the parser reads).
BNP_ENTRY = {
    "instrumentID": 1238,
    "instrumentDisplayName": "BNP Paribas SA",
    "instrumentTypeID": 5,
    "exchangeID": 9,
    "symbolFull": "BNP.PA",
    "priceSource": "Euronext",
}


class BrokerStub:
    def __init__(self, entries) -> None:
        self._entries = entries
        self.requested: list[list[int]] = []

    async def fetch(self, instrument_ids):
        self.requested.append(list(instrument_ids))
        return {"instrumentDisplayDatas": self._entries}


@pytest.mark.anyio
async def test_a_catalog_entry_becomes_an_identity_with_provenance() -> None:
    service = InstrumentMetadataService(broker=BrokerStub([BNP_ENTRY]))

    described = await service.describe([1238])

    item = described[1238]

    assert item.symbol == "BNP.PA"
    assert item.name == "BNP Paribas SA"
    # Type id 5 is the same stock id the classifier already maps.
    assert item.asset_type_id == 5
    assert item.reading is not None
    assert item.reading.source == "eToro"


@pytest.mark.anyio
async def test_an_id_the_catalog_does_not_return_stays_absent() -> None:
    """The gap stays visible; nothing is filled with a lookalike."""

    service = InstrumentMetadataService(broker=BrokerStub([BNP_ENTRY]))

    described = await service.describe([1238, 99999])

    assert 1238 in described
    assert 99999 not in described


@pytest.mark.anyio
async def test_a_malformed_entry_is_skipped_not_guessed_at() -> None:
    service = InstrumentMetadataService(
        broker=BrokerStub(
            [
                {"instrumentID": 7, "symbolFull": ""},
                {"symbolFull": "NOID.X"},
                "not-a-dict",
                BNP_ENTRY,
            ]
        )
    )

    described = await service.describe([7, 1238])

    assert set(described) == {1238}


@pytest.mark.anyio
async def test_an_entry_without_a_type_classifies_as_unknown() -> None:
    entry = dict(BNP_ENTRY)
    del entry["instrumentTypeID"]

    service = InstrumentMetadataService(broker=BrokerStub([entry]))

    described = await service.describe([1238])

    # 0 is outside the mapped ids, so the class reads UNKNOWN — the
    # honest reading of a catalog entry that did not say.
    assert described[1238].asset_type_id == 0


@pytest.mark.anyio
async def test_nothing_wanted_means_nothing_fetched() -> None:
    broker = BrokerStub([])
    service = InstrumentMetadataService(broker=broker)

    assert await service.describe([]) == {}
    assert broker.requested == []


# ------------------------------------------------------------------
# The resolver: watchlists first, the catalog only for what they miss.
# ------------------------------------------------------------------


def watched(instrument_id: int, symbol: str) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=symbol,
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=0,
        rank=1,
        avatar_url=None,
    )


class WatchlistServiceStub:
    def __init__(self, items: dict[int, WatchlistItem]) -> None:
        self._items = items

    async def get(self):
        from app.domain.watchlist import Watchlist

        return (
            Watchlist(
                watchlist_id="w1",
                name="Stub",
                watchlist_type="custom",
                is_default=False,
                rank=1,
                items=tuple(self._items.values()),
            ),
        )


class MetadataServiceStub:
    def __init__(self, described: dict[int, WatchlistItem]) -> None:
        self._described = described
        self.asked: list[list[int]] = []

    async def describe(self, instrument_ids):
        self.asked.append(sorted(instrument_ids))
        return {
            key: value
            for key, value in self._described.items()
            if key in set(instrument_ids)
        }


class FailingMetadataServiceStub:
    async def describe(self, instrument_ids):
        raise RuntimeError("catalog unreachable")


def resolver(
    watchlists: dict[int, WatchlistItem],
    metadata,
) -> InstrumentSymbolResolver:
    return InstrumentSymbolResolver(
        watchlist_service=WatchlistServiceStub(watchlists),  # type: ignore[arg-type]
        metadata_service=metadata,
    )


@pytest.mark.anyio
async def test_the_catalog_is_asked_only_about_unwatched_ids() -> None:
    metadata = MetadataServiceStub({1238: watched(1238, "BNP.PA")})

    items = await resolver({1016: watched(1016, "DIS")}, metadata).items_for(
        [1016, 1238]
    )

    assert set(items) == {1016, 1238}
    assert items[1238].symbol == "BNP.PA"
    # The watched id was never re-asked about.
    assert metadata.asked == [[1238]]


@pytest.mark.anyio
async def test_fully_watched_holdings_need_no_catalog_call() -> None:
    metadata = MetadataServiceStub({})

    await resolver({1016: watched(1016, "DIS")}, metadata).items_for([1016])

    assert metadata.asked == []


@pytest.mark.anyio
async def test_an_unreachable_catalog_degrades_to_the_watchlist_view() -> None:
    """The holding keeps its placeholder — an honest absence, not a
    failed cycle."""

    items = await resolver(
        {1016: watched(1016, "DIS")},
        FailingMetadataServiceStub(),
    ).items_for([1016, 1238])

    assert set(items) == {1016}
