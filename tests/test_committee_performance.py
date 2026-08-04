from datetime import datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)


def test_empty_performance(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    performance = CommitteeAnalyticsService(
        repository,
    ).performance()

    assert performance.recommendations == 0
    assert performance.completed == 0
    assert performance.successful == 0
    assert performance.accuracy == 0


def test_performance_from_outcomes(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    for index in range(5):
        repository.save(
            Event(
                timestamp=datetime(2026, 7, 20, 9, index),
                event_type=EventType.RECOMMENDATION_GENERATED,
                symbol="SPY",
                payload={
                    "recommendation": "BUY",
                    "confidence": 80,
                },
            )
        )

    outcomes = [True, True, False, True]

    for index, successful in enumerate(outcomes):
        repository.save(
            Event(
                timestamp=datetime(2026, 7, 27, 9, index),
                event_type=(EventType.RECOMMENDATION_OUTCOME_RECORDED),
                symbol="SPY",
                payload={
                    "successful": successful,
                },
            )
        )

    performance = CommitteeAnalyticsService(
        repository,
    ).performance()

    assert performance.recommendations == 5
    assert performance.completed == 4
    assert performance.successful == 3
    assert performance.accuracy == 75
