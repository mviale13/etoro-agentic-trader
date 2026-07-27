from app.domain.committee_member_weight import (
    CommitteeMemberWeight,
)
from app.repositories.event_repository import EventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)


class CommitteeWeightService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def weights(
        self,
    ) -> list[CommitteeMemberWeight]:
        performance = CommitteeAnalyticsService(
            self._repository,
        ).member_performance()

        return [
            CommitteeMemberWeight(
                member=item.member,
                accuracy=item.accuracy,
                weight=item.accuracy / 100,
            )
            for item in performance
        ]
