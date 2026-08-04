from datetime import UTC, datetime

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.recommendation_replay_service import (
    RecommendationReplayService,
)


def test_latest_recommendation_without_outcome(tmp_path):
    repository = JsonEventRepository(tmp_path)

    timestamp = datetime.now(UTC)

    repository.save(
        Event(
            timestamp=timestamp,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="MSFT",
            payload={},
        )
    )

    replay = RecommendationReplayService(repository).latest()

    assert len(replay) == 1
    assert replay[0].recommendation.symbol == "MSFT"
    assert replay[0].outcome is None
