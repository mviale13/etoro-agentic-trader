from datetime import UTC, datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_weight_service import (
    CommitteeWeightService,
)


def test_empty_weights(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    assert (
        CommitteeWeightService(
            repository,
        ).weights()
        == []
    )


def test_weight_equals_accuracy(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    recommendation_timestamp = datetime(2026, 7, 20, 9, tzinfo=UTC)

    repository.save(
        Event(
            timestamp=recommendation_timestamp,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="MSFT",
            payload={
                "recommendation": "BUY",
                "votes": [
                    {
                        "member": "Momentum",
                        "vote": "BUY",
                        "confidence": 80,
                        "rationale": "",
                    }
                ],
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 9, tzinfo=UTC),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="MSFT",
            payload={
                "recommendation_timestamp": recommendation_timestamp.isoformat(),
                "return_pct": 10,
                "successful": True,
            },
        )
    )

    weights = CommitteeWeightService(
        repository,
    ).weights()

    assert len(weights) == 1
    assert weights[0].member == "Momentum"
    assert weights[0].accuracy == 100
    assert weights[0].weight == 1.0
