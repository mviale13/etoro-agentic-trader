from datetime import UTC, datetime

from app.domain.provenance import Provenance
from app.services.etoro_watchlist_parser import EtoroWatchlistParser


def test_parser_builds_watchlists_and_instrument_items() -> None:
    body = {
        "status": 200,
        "watchlists": [
            {
                "watchlistId": "watchlist-1",
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
        ],
    }

    watchlists = EtoroWatchlistParser.parse(body)

    assert len(watchlists) == 1

    watchlist = watchlists[0]

    assert watchlist.watchlist_id == "watchlist-1"
    assert watchlist.name == "Recently Invested"
    assert watchlist.watchlist_type == "RecentlyInvested"
    assert watchlist.is_default is False
    assert len(watchlist.items) == 1

    item = watchlist.items[0]

    assert item.instrument_id == 1004
    assert item.symbol == "MSFT"
    assert item.name == "Microsoft"
    assert item.avatar_url == "https://example.com/msft.png"


def test_parser_ignores_non_instrument_and_invalid_items() -> None:
    body = {
        "watchlists": [
            {
                "watchlistId": "watchlist-1",
                "name": "Ideas",
                "watchlistType": "Custom",
                "items": [
                    {
                        "itemId": 1,
                        "itemType": "Person",
                    },
                    {
                        "itemId": 2,
                        "itemType": "Instrument",
                        "market": {
                            "symbolName": "",
                            "displayName": "",
                        },
                    },
                ],
            }
        ]
    }

    watchlists = EtoroWatchlistParser.parse(body)

    assert len(watchlists) == 1
    assert watchlists[0].items == ()


def test_parser_returns_empty_tuple_for_missing_watchlists() -> None:
    assert EtoroWatchlistParser.parse({}) == ()


def test_parser_stamps_each_item_with_the_identity_reading() -> None:
    reading = Provenance(
        source="eToro",
        observed_at=datetime(2026, 8, 4, 9, 30, tzinfo=UTC),
    )
    body = {
        "watchlists": [
            {
                "watchlistId": "watchlist-1",
                "name": "Recently Invested",
                "items": [
                    {
                        "itemId": 1004,
                        "itemType": "Instrument",
                        "market": {
                            "symbolName": "MSFT",
                            "displayName": "Microsoft",
                        },
                    }
                ],
            }
        ],
    }

    watchlists = EtoroWatchlistParser.parse(body, reading)

    assert watchlists[0].items[0].reading is reading


def test_parser_leaves_the_reading_absent_when_none_is_given() -> None:
    body = {
        "watchlists": [
            {
                "items": [
                    {
                        "itemId": 1004,
                        "itemType": "Instrument",
                        "market": {
                            "symbolName": "MSFT",
                            "displayName": "Microsoft",
                        },
                    }
                ],
            }
        ],
    }

    watchlists = EtoroWatchlistParser.parse(body)

    assert watchlists[0].items[0].reading is None
