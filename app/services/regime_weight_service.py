from app.domain.market_regime import MarketRegimeType
from app.repositories.event_repository import EventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)


class RegimeWeightService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def weights(
        self,
        regime: MarketRegimeType,
    ) -> dict[str, float]:
        performance = CommitteeAnalyticsService(
            self._repository,
        ).member_performance_by_regime()

        return {
            item.member: item.accuracy / 100
            for item in performance
            if item.regime == regime
        }
