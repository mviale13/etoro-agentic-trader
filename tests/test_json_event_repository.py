import json
from datetime import UTC, datetime
from pathlib import Path

from app.domain.event import Event
from app.repositories.json_event_repository import (
    JsonEventRepository,
)


def test_save_and_load_event(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    event = Event(
        timestamp=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
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
            timestamp=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
            event_type="first",
            symbol="MSFT",
            payload={},
        )
    )

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
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


def test_one_undated_event_does_not_take_the_journal_down(tmp_path: Path) -> None:
    """
    The outage this repair exists for, reproduced.

    One writer stamped `datetime.now()` with no zone. From the moment
    that single event reached the journal, sorting it raised
    `TypeError: can't compare offset-naive and offset-aware datetimes` —
    so `load_all` raised, so every page built on the Brain returned a
    500, and it stayed that way because nothing that reads the journal
    could get past the record. One event out of 475.

    A journal is the one store that has to survive its own history: it
    is append-only and it is never re-read from anywhere else.
    """

    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
            event_type="recommendation_generated",
            symbol="MSFT",
            payload={},
        )
    )

    # Written the way the defective writer wrote it, straight to disk.
    path = next(tmp_path.glob("*.json"))
    records = json.loads(path.read_text(encoding="utf-8"))
    records.append(
        {
            "timestamp": "2026-07-27T09:00:00",
            "event_type": "memory_recorded",
            "symbol": None,
            "payload": {},
        }
    )
    path.write_text(json.dumps(records), encoding="utf-8")

    events = repository.load_all()

    assert len(events) == 2

    # Read as UTC, so it orders against every aware event beside it.
    assert events[1].timestamp == datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
