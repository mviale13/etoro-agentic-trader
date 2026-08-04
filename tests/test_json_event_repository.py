from datetime import datetime
from pathlib import Path

from app.domain.event import Event
from app.repositories.json_event_repository import (
    JsonEventRepository,
)


def test_save_and_load_event(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    event = Event(
        timestamp=datetime(2026, 7, 27, 8, 0),
        event_type="recommendation_generated",
        symbol="MSFT",
        payload={
            "recommendation": "BUY",
            "confidence": 87,
        },
    )

    repository.save(event)

    events = repository.load_all()

    assert len(events) == 1
    assert events[0] == event


def test_load_latest(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 8, 0),
            event_type="first",
            symbol="MSFT",
            payload={},
        )
    )

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 9, 0),
            event_type="second",
            symbol="AAPL",
            payload={},
        )
    )

    latest = repository.load_latest()

    assert len(latest) == 1
    assert latest[0].event_type == "second"


def test_empty_repository(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    assert repository.load_all() == []
    assert repository.load_latest() == []
