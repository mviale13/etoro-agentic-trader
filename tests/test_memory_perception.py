from datetime import UTC, datetime
from pathlib import Path

from app.application.brain.perception.memory_perception import (
    MemoryPerception,
)
from app.application.learning.decision_journal import DecisionJournal
from app.brain import BrainBuilder
from app.cio.decision_state import DecisionState
from app.repositories.json_event_repository import JsonEventRepository
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)
from tests.test_decision_journal import make_decision


def test_memory_perception_reports_recorded_decisions(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    DecisionJournal(repository).record(
        make_decision(
            symbol="MSFT",
            state=DecisionState.MONITOR,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )

    history = MemoryPerception(repository=repository).execute()

    assert set(history) == {"MSFT"}
    assert history["MSFT"].current_state is DecisionState.MONITOR


def test_memory_perception_reports_nothing_when_nothing_was_decided(
    tmp_path: Path,
) -> None:
    perception = MemoryPerception(
        repository=JsonEventRepository(tmp_path),
    )

    assert perception.execute() == {}


def test_the_brain_carries_the_recorded_history(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    DecisionJournal(repository).record(make_decision(symbol="MSFT"))

    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        decision_history=MemoryPerception(repository=repository).execute(),
    ).build()

    assert brain.decision_history_for("msft").current_state is (DecisionState.RECOMMEND)


def test_an_unjudged_symbol_reports_an_empty_history() -> None:
    brain = BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
    ).build()

    history = brain.decision_history_for("NVDA")

    assert history.symbol == "NVDA"
    assert history.is_empty
