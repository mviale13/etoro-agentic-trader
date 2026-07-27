from datetime import UTC, datetime

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.recommendation_timeline_service import (
    RecommendationTimelineService,
)


def test_latest_timeline(tmp_path):
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime.now(UTC),
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="MSFT",
            payload={},
        )
    )

    timeline = RecommendationTimelineService(
        repository,
    ).latest()

    assert len(timeline.items) == 1
    assert timeline.items[0].recommendation.symbol == "MSFT"
