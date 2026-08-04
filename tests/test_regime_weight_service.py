from datetime import UTC, datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.domain.market_regime import MarketRegimeType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.regime_weight_service import (
    RegimeWeightService,
)


def test_regime_weights(
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
                "recommendation_timestamp": recommendation_time.isoformat(),
                "return_pct": 10.0,
                "successful": True,
            },
        )
    )

    weights = RegimeWeightService(
        repository,
    ).weights(
        MarketRegimeType.BULL,
    )

    assert weights["Momentum"] == 1.0
