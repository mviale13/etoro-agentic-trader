from typing import Any, Protocol

from app.brokers.etoro_watchlist import EtoroWatchlistBroker
from app.config import Settings
from app.domain.recommendation import Recommendation
from app.domain.watchlist import Watchlist
from app.domain.watchlist_item import WatchlistItem
from app.services.committee_service import CommitteeService
from app.services.etoro_watchlist_parser import EtoroWatchlistParser


class WatchlistProvider(Protocol):
    async def fetch(self) -> dict[str, Any]: ...


class WatchlistService:
    WATCHLIST = [
        "MSFT",
        "ASML",
        "GOOGL",
        "META",
        "AMZN",
    ]

    def __init__(
        self,
        broker: WatchlistProvider | None = None,
    ) -> None:
        self._broker = broker or EtoroWatchlistBroker(
            Settings(),
        )

    async def get(self) -> tuple[Watchlist, ...]:
        body = await self._broker.fetch()
        return EtoroWatchlistParser.parse(body)

    async def find_symbol(
        self,
        symbol: str,
    ) -> WatchlistItem | None:
        normalized = symbol.upper().strip()
        watchlists = await self.get()

        for watchlist in watchlists:
            for item in watchlist.items:
                if item.symbol.upper() == normalized:
                    return item

        return None

    async def build(self) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        committee = CommitteeService()

        for symbol in self.WATCHLIST:
            recommendation = await committee.evaluate(symbol)
            recommendations.append(recommendation)

        recommendations.sort(
            key=lambda recommendation: recommendation.decision.confidence,
            reverse=True,
        )

        return recommendations
