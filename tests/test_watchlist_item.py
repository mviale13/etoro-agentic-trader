from app.domain.watchlist_item import WatchlistItem


def test_watchlist_item_stores_instrument_metadata() -> None:
    item = WatchlistItem(
        instrument_id=1004,
        symbol="MSFT",
        name="Microsoft",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=1,
        avatar_url="https://example.com/msft.png",
    )

    assert item.instrument_id == 1004
    assert item.symbol == "MSFT"
    assert item.name == "Microsoft"
    assert item.asset_type_id == 5
    assert item.exchange_id == 4
    assert item.rank == 1
