from app.domain.recommendation_timeline import RecommendationTimeline
from app.repositories.event_repository import EventRepository
from app.services.recommendation_replay_service import (
    RecommendationReplayService,
)


class RecommendationTimelineService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def latest(
        self,
        limit: int = 20,
    ) -> RecommendationTimeline:
        items = RecommendationReplayService(
            self._repository,
        ).latest(limit)

        return RecommendationTimeline(
            items=tuple(items),
        )
