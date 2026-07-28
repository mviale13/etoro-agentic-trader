from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class WatchlistItem:
    instrument_id: int
    symbol: str
    name: str
    asset_type_id: int
    asset_type_subcategory_id: int
    exchange_id: int
    rank: int
    avatar_url: str | None
