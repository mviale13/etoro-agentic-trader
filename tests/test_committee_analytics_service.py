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


def test_empty_statistics(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    stats = CommitteeAnalyticsService(
        repository,
    ).statistics()

    assert stats.recommendations == 0
    assert stats.average_confidence == 0


def test_statistics(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime.now(),
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="SPY",
            payload={
                "recommendation": "BUY",
                "confidence": 80,
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime.now(),
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="BTC",
            payload={
                "recommendation": "HOLD",
                "confidence": 90,
            },
        )
    )

    stats = CommitteeAnalyticsService(
        repository,
    ).statistics()

    assert stats.recommendations == 2
    assert stats.buy == 1
    assert stats.hold == 1
    assert stats.sell == 0
    assert stats.average_confidence == 85
