from dataclasses import dataclass

from app.domain.watchlist_item import WatchlistItem


@dataclass(frozen=True, slots=True)
class Watchlist:
    watchlist_id: str
    name: str
    watchlist_type: str
    is_default: bool
    rank: int
    items: tuple[WatchlistItem, ...]
