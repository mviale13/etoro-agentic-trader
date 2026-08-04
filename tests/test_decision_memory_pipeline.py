from datetime import UTC, datetime
from pathlib import Path

from app.application.brain.perception.memory_perception import (
    MemoryPerception,
)
from app.application.learning.decision_journal import DecisionJournal
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.brain import Brain, BrainBuilder
from app.cio.decision_state import DecisionState
from app.repositories.json_event_repository import JsonEventRepository
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)
from tests.test_decision_journal import make_decision


def make_brain(
    repository: JsonEventRepository | None = None,
) -> Brain:
    history = (
        MemoryPerception(repository=repository).execute()
        if repository is not None
        else {}
    )

    return BrainBuilder(
        portfolio=make_portfolio(),
        market=make_market(),
        investment_policy=make_policy(),
        decision_history=history,
    ).build()


def test_the_pipeline_only_remembers_when_it_is_given_a_journal() -> None:
    assert ExecutivePipeline().journal is None


def test_the_decision_is_recorded(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    workspace = ExecutivePipeline(
        journal=DecisionJournal(repository),
    ).execute(
        symbol="MSFT",
        brain=make_brain(),
    )

    assert workspace.decision is not None

    history = DecisionJournal(repository).history("MSFT")

    assert history.total == 1
    assert history.current_state is workspace.decision.state


def test_a_first_decision_claims_no_history(tmp_path: Path) -> None:
    workspace = ExecutivePipeline(
        journal=DecisionJournal(JsonEventRepository(tmp_path)),
    ).execute(
        symbol="MSFT",
        brain=make_brain(),
    )

    assert workspace.thesis is not None
    assert workspace.thesis.previous_decisions is None


def test_the_next_cycle_states_what_was_decided_before(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    pipeline = ExecutivePipeline(journal=DecisionJournal(repository))

    first = pipeline.execute(
        symbol="MSFT",
        brain=make_brain(),
    )

    assert first.decision is not None

    second = pipeline.execute(
        symbol="MSFT",
        brain=make_brain(repository),
    )

    assert second.thesis is not None
    assert second.thesis.previous_decisions is not None
    assert first.decision.state.value in second.thesis.previous_decisions


def test_a_changed_decision_says_what_it_changed_from(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    decided = (
        ExecutivePipeline()
        .execute(
            symbol="MSFT",
            brain=make_brain(),
        )
        .decision
    )

    assert decided is not None

    superseded = next(state for state in DecisionState if state is not decided.state)

    DecisionJournal(repository).record(
        make_decision(
            symbol="MSFT",
            state=superseded,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        )
    )

    workspace = ExecutivePipeline().execute(
        symbol="MSFT",
        brain=make_brain(repository),
    )

    assert workspace.thesis is not None
    assert workspace.thesis.previous_decisions is not None
    assert workspace.thesis.previous_decisions.startswith(
        f"Changed from {superseded.value} to {decided.state.value}."
    )
    assert "2026-07-28" in workspace.thesis.previous_decisions
