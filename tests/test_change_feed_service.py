from datetime import UTC, datetime
from pathlib import Path

from app.application.change_feed.change_feed_service import ChangeFeedService
from app.application.learning.decision_journal import DecisionJournal
from app.cio.decision_state import DecisionState
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeSeverity,
)
from app.repositories.json_event_repository import JsonEventRepository
from tests.test_decision_journal import make_decision


def make_service(tmp_path: Path) -> tuple[ChangeFeedService, DecisionJournal]:
    journal = DecisionJournal(JsonEventRepository(tmp_path))

    return ChangeFeedService(journal=journal), journal


def test_nothing_recorded_reports_no_changes(tmp_path: Path) -> None:
    service, _ = make_service(tmp_path)

    assert service.build().events == ()


def test_an_unchanged_decision_is_not_a_change(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
        )
    )

    assert service.build().events == ()


def test_a_changed_decision_is_reported(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
        )
    )

    feed = service.build()

    assert feed.total == 1

    change = feed.events[0]

    assert change.title == "MSFT moved from MONITOR to PREPARE"
    assert change.description == "The investment case satisfies every gate."
    assert change.category is ChangeCategory.DECISION
    assert change.timestamp == datetime(2026, 7, 30, 9, 0, tzinfo=UTC)
    assert change.action_required is True
    assert feed.action_required is True


def test_severity_measures_how_far_the_decision_moved(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    for index, state in enumerate(
        (
            DecisionState.REJECT,
            DecisionState.MONITOR,
            DecisionState.PREPARE,
            DecisionState.REJECT,
        )
    ):
        journal.record(
            make_decision(
                state=state,
                decided_at=datetime(2026, 7, 28 + index, 9, 0, tzinfo=UTC),
            )
        )

    severities = [change.severity for change in reversed(service.build().events)]

    assert severities == [
        ChangeSeverity.LOW,
        ChangeSeverity.MEDIUM,
        ChangeSeverity.HIGH,
    ]


def test_changes_are_reported_newest_first(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    journal.record(
        make_decision(
            symbol="MSFT",
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            symbol="MSFT",
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            symbol="NVDA",
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            symbol="NVDA",
            state=DecisionState.INVESTIGATE,
            decided_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        )
    )

    titles = [change.title for change in service.build().events]

    assert titles == [
        "NVDA moved from MONITOR to INVESTIGATE",
        "MSFT moved from MONITOR to PREPARE",
    ]


def test_the_feed_can_be_narrowed_to_the_symbols_held(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    for symbol in ("MSFT", "NVDA"):
        journal.record(
            make_decision(
                symbol=symbol,
                state=DecisionState.MONITOR,
                decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
            )
        )
        journal.record(
            make_decision(
                symbol=symbol,
                state=DecisionState.PREPARE,
                decided_at=datetime(2026, 7, 29, 9, 0, tzinfo=UTC),
            )
        )

    feed = service.build(symbols=["msft"])

    assert [change.title for change in feed.events] == [
        "MSFT moved from MONITOR to PREPARE"
    ]


def test_the_feed_is_capped(tmp_path: Path) -> None:
    service, journal = make_service(tmp_path)

    states = (
        DecisionState.REJECT,
        DecisionState.MONITOR,
        DecisionState.INVESTIGATE,
        DecisionState.PREPARE,
    )

    for index, state in enumerate(states):
        journal.record(
            make_decision(
                state=state,
                decided_at=datetime(2026, 7, 28 + index, 9, 0, tzinfo=UTC),
            )
        )

    assert service.build(limit=2).total == 2
