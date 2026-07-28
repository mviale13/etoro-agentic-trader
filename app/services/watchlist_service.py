from app.brokers.etoro_watchlist import EtoroWatchlistBroker
from app.config import Settings
from app.domain.recommendation import Recommendation
from app.domain.watchlist import Watchlist
from app.services.committee_service import CommitteeService
from app.services.etoro_watchlist_parser import EtoroWatchlistParser


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
        broker: EtoroWatchlistBroker | None = None,
    ) -> None:
        self._broker = broker or EtoroWatchlistBroker(
            Settings(),
        )

    async def get(self) -> tuple[Watchlist, ...]:
        body = await self._broker.fetch()
        return EtoroWatchlistParser.parse(body)

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
