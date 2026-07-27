from datetime import UTC, datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.domain.market_regime import MarketRegimeType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.committee_analytics_service import (
    CommitteeAnalyticsService,
)


def test_member_performance_by_regime(
    tmp_path: Path,
) -> None:
    repository = JsonEventRepository(tmp_path)
    recommendation_time = datetime.now(UTC)

    repository.save(
        Event(
            timestamp=recommendation_time,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="MSFT",
            payload={
                "regime": "BULL",
                "votes": [
                    {
                        "member": "Momentum",
                        "vote": "BUY",
                    }
                ],
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime.now(UTC),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="MSFT",
            payload={
                "recommendation_timestamp": (recommendation_time.isoformat()),
                "return_pct": 8.5,
                "successful": True,
            },
        )
    )

    performance = CommitteeAnalyticsService(
        repository,
    ).member_performance_by_regime()

    assert len(performance) == 1

    item = performance[0]

    assert item.member == "Momentum"
    assert item.regime == MarketRegimeType.BULL
    assert item.completed == 1
    assert item.successful == 1
    assert item.accuracy == 100


def test_unknown_regime_defaults_to_sideways(
    tmp_path: Path,
) -> None:
    repository = JsonEventRepository(tmp_path)
    recommendation_time = datetime.now(UTC)

    repository.save(
        Event(
            timestamp=recommendation_time,
            event_type=EventType.RECOMMENDATION_GENERATED,
            symbol="SPY",
            payload={
                "regime": "UNKNOWN",
                "votes": [
                    {
                        "member": "Risk",
                        "vote": "HOLD",
                    }
                ],
            },
        )
    )

    repository.save(
        Event(
            timestamp=datetime.now(UTC),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="SPY",
            payload={
                "recommendation_timestamp": (recommendation_time.isoformat()),
                "return_pct": 1.0,
                "successful": True,
            },
        )
    )

    performance = CommitteeAnalyticsService(
        repository,
    ).member_performance_by_regime()

    assert len(performance) == 1
    assert performance[0].member == "Risk"
    assert performance[0].regime == MarketRegimeType.SIDEWAYS
    assert performance[0].accuracy == 100
