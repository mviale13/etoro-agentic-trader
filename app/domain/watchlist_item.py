from dataclasses import dataclass

from app.domain.provenance import Provenance


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

    #: Where this instrument's identity came from, and when. The watchlist
    #: is the only place the symbol and name are read, so it is the only
    #: place their age can be stamped. None where the item was constructed
    #: without a fetch behind it.
    reading: Provenance | None = None
