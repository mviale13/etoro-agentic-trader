from typing import Any

from app.domain.provenance import Provenance
from app.domain.watchlist import Watchlist
from app.domain.watchlist_item import WatchlistItem


class EtoroWatchlistParser:
    @classmethod
    def parse(
        cls,
        body: dict[str, Any],
        reading: Provenance | None = None,
    ) -> tuple[Watchlist, ...]:
        raw_watchlists = body.get("watchlists")

        if not isinstance(raw_watchlists, list):
            return ()

        watchlists: list[Watchlist] = []

        for raw_watchlist in raw_watchlists:
            if not isinstance(raw_watchlist, dict):
                continue

            watchlists.append(
                Watchlist(
                    watchlist_id=str(raw_watchlist.get("watchlistId", "")),
                    name=str(raw_watchlist.get("name", "")),
                    watchlist_type=str(raw_watchlist.get("watchlistType", "")),
                    is_default=bool(raw_watchlist.get("isDefault", False)),
                    rank=cls._integer(raw_watchlist.get("watchlistRank")),
                    items=cls._parse_items(raw_watchlist.get("items"), reading),
                )
            )

        return tuple(watchlists)

    @classmethod
    def _parse_items(
        cls,
        raw_items: Any,
        reading: Provenance | None = None,
    ) -> tuple[WatchlistItem, ...]:
        if not isinstance(raw_items, list):
            return ()

        items: list[WatchlistItem] = []

        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue

            if raw_item.get("itemType") != "Instrument":
                continue

            market = raw_item.get("market")

            if not isinstance(market, dict):
                continue

            symbol = str(market.get("symbolName", "")).strip()
            name = str(market.get("displayName", "")).strip()

            if not symbol or not name:
                continue

            items.append(
                WatchlistItem(
                    instrument_id=cls._integer(raw_item.get("itemId")),
                    symbol=symbol.upper(),
                    name=name,
                    asset_type_id=cls._integer(market.get("assetTypeId")),
                    asset_type_subcategory_id=cls._integer(
                        market.get("assetTypeSubCategoryId")
                    ),
                    exchange_id=cls._integer(market.get("exchangeId")),
                    rank=cls._integer(raw_item.get("itemRank")),
                    avatar_url=cls._avatar_url(market.get("avatar")),
                    reading=reading,
                )
            )

        return tuple(items)

    @staticmethod
    def _avatar_url(raw_avatar: Any) -> str | None:
        if not isinstance(raw_avatar, dict):
            return None

        for size in ("medium", "small", "large"):
            value = raw_avatar.get(size)

            if isinstance(value, str) and value:
                return value

        return None

    @staticmethod
    def _integer(value: Any, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
