from app.domain.recommendation import Recommendation
from app.services.committee_service import CommitteeService


class WatchlistService:
    WATCHLIST = [
        "MSFT",
        "ASML",
        "GOOGL",
        "META",
        "AMZN",
    ]

    async def build(self) -> list[Recommendation]:
        recommendations: list[Recommendation] = []

        committee = CommitteeService()

        for symbol in self.WATCHLIST:
            recommendation = await committee.evaluate(symbol)
            recommendations.append(recommendation)

        recommendations.sort(
            key=lambda r: r.decision.confidence,
            reverse=True,
        )

        return recommendations
