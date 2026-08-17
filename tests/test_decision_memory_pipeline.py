from datetime import UTC, datetime
from pathlib import Path

from app.application.brain.perception.memory_perception import (
    MemoryPerception,
)
from app.application.learning.decision_journal import DecisionJournal
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.brain import Brain, BrainBuilder
from app.cio.decision_state import DecisionState
from app.domain.decision_history import TrendDirection
from app.repositories.json_event_repository import JsonEventRepository
from tests.test_brain_context import (
    make_market,
    make_policy,
    make_portfolio,
)
from tests.test_decision_journal import make_decision
from tests.test_security_evidence import make_company


def make_brain(
    repository: JsonEventRepository | None = None,
    evidenced: bool = False,
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
        # A security the signals found something in favour of. A case
        # citing no supporting reason now carries no conviction at all,
        # so a test about conviction *moving* needs one to move.
        evidence={"MSFT": (make_company("MSFT"),)} if evidenced else {},
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

    # A first review is not a stable one: with nothing recorded there is
    # no direction to report, and claiming one would invent a history.
    assert workspace.thesis.trend is None


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
    assert second.thesis.trend is not None

    # Same decision twice running: the case is holding, and the count
    # includes today's — the cycle records it after the thesis is built.
    assert second.thesis.trend.direction is TrendDirection.STABLE
    assert "2 consecutive reviews" in second.thesis.trend.stated


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

    trend = workspace.thesis.trend

    assert trend is not None
    assert f"{superseded.value} → {decided.state.value}" in trend.stated

    # Which way it moved is read off the lifecycle ranks, not judged.
    expected = (
        TrendDirection.IMPROVING
        if decided.state.lifecycle_rank > superseded.lifecycle_rank
        else TrendDirection.DETERIORATING
    )

    assert trend.direction is expected


def test_the_scores_a_decision_was_made_on_are_recorded_with_it(
    tmp_path: Path,
) -> None:
    """
    Without them a later cycle can say the conviction moved, never why.

    That is exactly what every decision recorded before this could say,
    and the reason the journal now writes the scores down.
    """

    repository = JsonEventRepository(tmp_path)
    pipeline = ExecutivePipeline(journal=DecisionJournal(repository))

    workspace = pipeline.execute(symbol="MSFT", brain=make_brain())

    assert workspace.evidence is not None

    recorded = DecisionJournal(repository).history("MSFT").latest

    assert recorded is not None
    assert recorded.scores.is_empty is False
    assert recorded.scores.evidence == workspace.evidence.evidence_score
    assert recorded.scores.safety == workspace.evidence.safety_score


def test_a_conviction_that_moved_says_which_scores_moved_under_it(
    tmp_path: Path,
) -> None:
    """The whole point: the dashboard stops being static."""

    from app.cio.executive_decision import DecisionEvidence

    repository = JsonEventRepository(tmp_path)

    # An earlier decision, recorded with the scores it stood on — which is
    # what makes the next one able to say what moved.
    DecisionJournal(repository).record(
        make_decision(
            symbol="MSFT",
            state=DecisionState.PREPARE,
            decided_at=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        ),
        DecisionEvidence(
            symbol="MSFT",
            quality_score=40,
            evidence_score=50,
            valuation_score=25,
            risk_score=65,
            portfolio_fit_score=60,
        ),
    )

    workspace = ExecutivePipeline().execute(
        symbol="MSFT",
        brain=make_brain(repository, evidenced=True),
    )

    assert workspace.thesis is not None

    change = workspace.thesis.conviction_change

    assert change is not None
    assert change.unexplained is False

    # Every reason names a score and quotes both ends of its move.
    assert change.because
    assert all("→" in line for line in change.because)
