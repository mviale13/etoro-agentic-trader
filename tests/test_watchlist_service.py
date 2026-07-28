from typing import Any

import pytest

from app.services.watchlist_service import WatchlistService


class FakeWatchlistBroker:
    async def fetch(self) -> dict[str, Any]:
        return {
            "watchlists": [
                {
                    "watchlistId": "recent",
                    "name": "Recently Invested",
                    "watchlistType": "RecentlyInvested",
                    "isDefault": False,
                    "watchlistRank": 0,
                    "items": [
                        {
                            "itemId": 1004,
                            "itemType": "Instrument",
                            "itemRank": 1,
                            "market": {
                                "symbolName": "MSFT",
                                "displayName": "Microsoft",
                                "assetTypeId": 5,
                                "assetTypeSubCategoryId": 0,
                                "exchangeId": 4,
                                "avatar": {
                                    "medium": "https://example.com/msft.png",
                                },
                            },
                        }
                    ],
                }
            ]
        }


@pytest.mark.anyio
async def test_find_symbol_returns_real_watchlist_item() -> None:
    service = WatchlistService(
        broker=FakeWatchlistBroker(),
    )

    item = await service.find_symbol("msft")

    assert item is not None
    assert item.instrument_id == 1004
    assert item.symbol == "MSFT"
    assert item.name == "Microsoft"


@pytest.mark.anyio
async def test_find_symbol_returns_none_when_missing() -> None:
    service = WatchlistService(
        broker=FakeWatchlistBroker(),
    )

    item = await service.find_symbol("UNKNOWN")

    assert item is None
