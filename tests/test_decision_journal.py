from datetime import UTC, datetime
from pathlib import Path

from app.application.learning.decision_journal import DecisionJournal
from app.cio.decision_state import DecisionState
from app.cio.executive_decision import ExecutiveDecision
from app.domain.event import Event
from app.repositories.json_event_repository import JsonEventRepository


def make_decision(
    symbol: str = "MSFT",
    state: DecisionState = DecisionState.RECOMMEND,
    decided_at: datetime | None = None,
    conviction: int = 80,
) -> ExecutiveDecision:
    return ExecutiveDecision(
        symbol=symbol,
        state=state,
        conviction=conviction,
        rationale="The investment case satisfies every gate.",
        decided_at=decided_at or datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
    )


def make_journal(tmp_path: Path) -> DecisionJournal:
    return DecisionJournal(JsonEventRepository(tmp_path))


def test_a_decision_is_remembered(tmp_path: Path) -> None:
    journal = make_journal(tmp_path)

    assert journal.record(make_decision()) is True

    history = journal.history("MSFT")

    assert history.total == 1
    assert history.current_state is DecisionState.RECOMMEND
    assert history.latest is not None
    assert history.latest.conviction == 80
    assert history.latest.rationale


def test_the_same_decision_is_not_recorded_twice_in_one_day(
    tmp_path: Path,
) -> None:
    journal = make_journal(tmp_path)

    journal.record(make_decision())

    repeated = make_decision(
        decided_at=datetime(2026, 8, 1, 17, 30, tzinfo=UTC),
    )

    assert journal.record(repeated) is False
    assert journal.history("MSFT").total == 1


def test_a_state_change_within_the_day_is_recorded(tmp_path: Path) -> None:
    journal = make_journal(tmp_path)

    journal.record(make_decision(state=DecisionState.MONITOR))

    changed = make_decision(
        state=DecisionState.RECOMMEND,
        decided_at=datetime(2026, 8, 1, 17, 30, tzinfo=UTC),
    )

    assert journal.record(changed) is True
    assert journal.history("MSFT").state_changes == 1


def test_history_reports_when_the_current_state_began(tmp_path: Path) -> None:
    journal = make_journal(tmp_path)

    journal.record(
        make_decision(
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.RECOMMEND,
            decided_at=datetime(2026, 7, 30, 9, 0, tzinfo=UTC),
        )
    )
    journal.record(
        make_decision(
            state=DecisionState.RECOMMEND,
            decided_at=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
        )
    )

    history = journal.history("MSFT")

    assert history.total == 3
    assert history.current_state is DecisionState.RECOMMEND
    assert history.previous_state is DecisionState.MONITOR
    assert history.current_state_since == datetime(2026, 7, 30, 9, 0, tzinfo=UTC)
    assert len(history.current_run) == 2


def test_a_symbol_without_records_reports_an_empty_history(
    tmp_path: Path,
) -> None:
    journal = make_journal(tmp_path)

    journal.record(make_decision(symbol="MSFT"))

    history = journal.history("NVDA")

    assert history.is_empty
    assert history.current_state is None
    assert history.current_state_since is None


def test_symbols_are_normalized(tmp_path: Path) -> None:
    journal = make_journal(tmp_path)

    journal.record(make_decision(symbol=" msft "))

    assert journal.history("MSFT").total == 1
    assert set(journal.histories()) == {"MSFT"}


def test_histories_are_grouped_by_symbol(tmp_path: Path) -> None:
    journal = make_journal(tmp_path)

    journal.record(make_decision(symbol="MSFT"))
    journal.record(make_decision(symbol="NVDA"))

    histories = journal.histories()

    assert set(histories) == {"MSFT", "NVDA"}
    assert histories["NVDA"].total == 1


def test_an_unreadable_record_is_skipped_rather_than_guessed(
    tmp_path: Path,
) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
            event_type="executive_decision_recorded",
            symbol="MSFT",
            payload={"state": "ACCUMULATE"},
        )
    )

    assert DecisionJournal(repository).history("MSFT").is_empty


def test_other_events_are_not_read_as_decisions(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime(2026, 8, 1, 9, 0, tzinfo=UTC),
            event_type="recommendation_generated",
            symbol="MSFT",
            payload={"recommendation": "BUY"},
        )
    )

    assert DecisionJournal(repository).histories() == {}
