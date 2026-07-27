from app.domain.event_type import EventType
from app.domain.recommendation_replay import RecommendationReplay
from app.repositories.event_repository import EventRepository


class RecommendationReplayService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def latest(
        self,
        limit: int = 10,
    ) -> list[RecommendationReplay]:
        recommendations = [
            event
            for event in self._repository.load_all()
            if event.event_type == EventType.RECOMMENDATION_GENERATED
        ]

        outcomes = [
            event
            for event in self._repository.load_all()
            if event.event_type == EventType.RECOMMENDATION_OUTCOME_RECORDED
        ]

        replays: list[RecommendationReplay] = []

        for recommendation in recommendations[-limit:]:
            outcome = next(
                (
                    item
                    for item in outcomes
                    if item.symbol == recommendation.symbol
                    and item.payload.get("recommendation_timestamp")
                    == recommendation.timestamp.isoformat()
                ),
                None,
            )

            replays.append(
                RecommendationReplay(
                    recommendation=recommendation,
                    outcome=outcome,
                )
            )

        return list(reversed(replays))
