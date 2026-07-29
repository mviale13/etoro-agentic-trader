"""Learning orchestration based on recorded investment outcomes."""

from app.domain.learning_insight import LearningInsight
from app.repositories.event_repository import EventRepository
from app.services.committee_analytics_service import CommitteeAnalyticsService


class LearningEngine:
    """Transform recommendation outcomes into actionable committee learning.

    The engine reads historical committee performance through the repository,
    evaluates member accuracy, and produces explainable weight recommendations.
    It does not mutate committee weights automatically: the investor remains in
    control of whether learning recommendations are applied.
    """

    def __init__(self, repository: EventRepository) -> None:
        self._repository = repository

    def learn(self) -> list[LearningInsight]:
        """Produce learning insights from historical committee performance."""
        performance = CommitteeAnalyticsService(
            self._repository,
        ).member_performance()

        insights: list[LearningInsight] = []

        for member in performance:
            if member.accuracy >= 85:
                recommendation = "Increase weight"
                reason = (
                    "High historical accuracy supports giving "
                    "this member more influence."
                )
            elif member.accuracy <= 65:
                recommendation = "Reduce weight"
                reason = (
                    "Historical accuracy suggests this member should contribute less."
                )
            else:
                recommendation = "Keep weight"
                reason = (
                    "Performance is stable and does not justify "
                    "changing the current weight."
                )

            insights.append(
                LearningInsight(
                    member=member.member,
                    recommendation=recommendation,
                    reason=reason,
                )
            )

        return insights

    def insights(self) -> list[LearningInsight]:
        """Compatibility verb for callers using the previous service API."""
        return self.learn()
