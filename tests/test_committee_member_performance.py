from datetime import datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)


def test_empty_member_performance(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    assert CommitteeAnalyticsService(repository).member_performance() == []


def test_members_are_scored_using_their_own_votes(
    tmp_path: Path,
) -> None:
    repository = JsonEventRepository(tmp_path)
    recommendation_timestamp = datetime(2026, 7, 20, 9, 0)

    repository.save(
        Event(
            timestamp=recommendation_timestamp,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="MSFT",
            payload={
                "recommendation": "BUY",
                "confidence": 80,
                "votes": [
                    {
                        "member": "Momentum",
                        "vote": "BUY",
                        "confidence": 80,
                        "rationale": "Positive momentum.",
                    },
                    {
                        "member": "Risk",
                        "vote": "SELL",
                        "confidence": 70,
                        "rationale": "Risk is elevated.",
                    },
                    {
                        "member": "Cash",
                        "vote": "HOLD",
                        "confidence": 75,
                        "rationale": "Wait for clarity.",
                    },
                ],
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 9, 0),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="MSFT",
            payload={
                "recommendation_timestamp": (recommendation_timestamp.isoformat()),
                "return_pct": 10.0,
                "successful": True,
            },
        )
    )

    performance = CommitteeAnalyticsService(repository).member_performance()

    momentum = next(item for item in performance if item.member == "Momentum")
    risk = next(item for item in performance if item.member == "Risk")
    cash = next(item for item in performance if item.member == "Cash")

    assert momentum.completed == 1
    assert momentum.successful == 1
    assert momentum.accuracy == 100

    assert risk.completed == 1
    assert risk.successful == 0
    assert risk.accuracy == 0

    assert cash.completed == 1
    assert cash.successful == 0
    assert cash.accuracy == 0


def test_hold_vote_succeeds_inside_tolerance(
    tmp_path: Path,
) -> None:
    repository = JsonEventRepository(tmp_path)
    recommendation_timestamp = datetime(2026, 7, 20, 9, 0)

    repository.save(
        Event(
            timestamp=recommendation_timestamp,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="SPY",
            payload={
                "recommendation": "HOLD",
                "confidence": 70,
                "votes": [
                    {
                        "member": "Risk",
                        "vote": "HOLD",
                        "confidence": 80,
                        "rationale": "Market remains uncertain.",
                    }
                ],
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 9, 0),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="SPY",
            payload={
                "recommendation_timestamp": (recommendation_timestamp.isoformat()),
                "return_pct": 1.5,
                "successful": True,
            },
        )
    )

    performance = CommitteeAnalyticsService(repository).member_performance()

    assert len(performance) == 1
    assert performance[0].member == "Risk"
    assert performance[0].successful == 1
    assert performance[0].accuracy == 100
