from datetime import UTC, datetime

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.learning_service import LearningService


def test_generates_learning_insights(tmp_path):
    repository = JsonEventRepository(tmp_path)

    recommendation_time = datetime.now(UTC)

    repository.save(
        Event(
            timestamp=recommendation_time,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="MSFT",
            payload={
                "votes": [
                    {
                        "member": "Momentum",
                        "vote": "BUY",
                        "confidence": 90,
                    }
                ]
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime.now(UTC),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="MSFT",
            payload={
                "recommendation_timestamp": recommendation_time.isoformat(),
                "return_pct": 10.0,
                "successful": True,
            },
        )
    )

    insights = LearningService(repository).insights()

    assert len(insights) == 1
    assert insights[0].member == "Momentum"
