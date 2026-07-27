from app.domain.learning_insight import LearningInsight
from app.repositories.event_repository import EventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)

"""
Transforms historical committee performance into
human-readable learning insights.
"""


class LearningService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def insights(
        self,
    ) -> list[LearningInsight]:
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
