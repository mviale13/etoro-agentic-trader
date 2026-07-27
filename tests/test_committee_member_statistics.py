from datetime import datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import (
    JsonEventRepository,
)
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)


def test_empty_member_statistics(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    statistics = CommitteeAnalyticsService(
        repository,
    ).member_statistics()

    assert statistics == []


def test_member_statistics(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime.now(),
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="SPY",
            payload={
                "recommendation": "BUY",
                "confidence": 80,
                "votes": [
                    {
                        "member": "Momentum",
                        "vote": "BUY",
                        "confidence": 80,
                        "rationale": "",
                    },
                    {
                        "member": "Risk",
                        "vote": "HOLD",
                        "confidence": 70,
                        "rationale": "",
                    },
                ],
            },
        )
    )

    statistics = CommitteeAnalyticsService(
        repository,
    ).member_statistics()

    assert len(statistics) == 2

    momentum = next(item for item in statistics if item.member == "Momentum")

    assert momentum.buy == 1
    assert momentum.hold == 0
    assert momentum.sell == 0
    assert momentum.average_confidence == 80

    risk = next(item for item in statistics if item.member == "Risk")

    assert risk.buy == 0
    assert risk.hold == 1
    assert risk.sell == 0
    assert risk.average_confidence == 70
