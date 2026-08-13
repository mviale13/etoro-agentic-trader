"""What the Artificial CIO decided before, and what moved when it changed.

The journal has held every transition since the platform began recording
decisions — it is what the home page's change feed is built from — while
the dossier said only *"Stable"*. Volkswagen's own record is the case
this exists for: on 9 August 2026 it moved PREPARE(76) → INVESTIGATE(70)
→ RECOMMEND(78) in five hours, and the dossier read *"Stable — 6
consecutive reviews since 2026-08-09"* — a stability claim dated to the
day the case moved twice.

The acceptance below runs against **committed** decision records —
`tests/fixtures/decision_journal/`, every `executive_decision_recorded`
event the platform had written when this slice was built, copied
verbatim.

That indirection is not tidiness. `data/events/` is **gitignored**: the
journal is a runtime artifact, unlike `data/knowledge/`, which the
repository tracks on purpose. A first draft of these tests read it
through `JsonEventRepository`'s path-literal default, passed on the
developer's machine, and failed under `git archive HEAD` — the trap
`CLAUDE.md` names, caught by the isolation run rather than by review. So
the evidence the acceptance names is committed beside it.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.application.learning.decision_journal import DecisionJournal
from app.cio.decision_state import DecisionState
from app.domain.decision_history import (
    DecisionHistory,
    DecisionRecord,
    RecordedScores,
)
from app.domain.score_basis import score_labels_for
from app.repositories.json_event_repository import JsonEventRepository

#: The committed decision records, named once and declared rather than
#: inherited: `JsonEventRepository` defaults to the path literal
#: `data/events`, which `conftest.py`'s hermetic root cannot redirect and
#: which git does not track.
COMMITTED_EVENTS = Path(__file__).resolve().parent / "fixtures" / "decision_journal"

START = datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def committed(symbol: str) -> DecisionHistory:
    """The decision history the repository has actually recorded."""

    return DecisionJournal(
        repository=JsonEventRepository(COMMITTED_EVENTS),
    ).history(symbol)


def record(
    state: DecisionState,
    conviction: int,
    *,
    day: int = 0,
    rationale: str = "Recorded at the time.",
    scores: RecordedScores | None = None,
) -> DecisionRecord:
    return DecisionRecord(
        symbol="EXAM",
        state=state,
        conviction=conviction,
        rationale=rationale,
        decided_at=START + timedelta(days=day),
        scores=scores if scores is not None else RecordedScores(),
    )


def history(*records: DecisionRecord) -> DecisionHistory:
    return DecisionHistory(symbol="EXAM", records=records)


# ── the acceptance: Volkswagen's own record ─────────────────────────


def test_the_recorded_flap_reaches_the_investor_with_its_cause() -> None:
    """Acceptance 1, against the committed journal.

    The dossier told the investor this case was stable. Its own record
    holds three states in five hours, and the reason the middle one
    happened: two scores stopped being measurable.
    """

    course = committed("VOW3.DE").course()

    assert course.reviews == 14
    assert course.changes == 8
    assert "changed 8 times" in course.stated

    ninth = [
        change
        for change in course.transitions
        if change.at.date().isoformat() == "2026-08-09"
    ]

    assert len(ninth) == 3, "three states were recorded on 9 August"

    # Most recent first, so this is the middle move of that day: the one
    # that took the case out of RECOMMEND territory.
    fell = next(
        change
        for change in ninth
        if change.from_state == "PREPARE" and change.to_state == "INVESTIGATE"
    )

    assert fell.from_conviction == 76
    assert fell.to_conviction == 70

    # The rationale the CIO recorded at the time, not a sentence written
    # now about a decision taken then.
    assert fell.rationale.startswith("Business quality has not been measured")

    assert "Business quality could no longer be measured (it was 62)" in fell.moved
    assert (
        "Valuation attractiveness could no longer be measured (it was 80)" in fell.moved
    )

    # And it came back three hours later, which is what makes the whole
    # episode a reading failure rather than a business one.
    recovered = next(
        change
        for change in ninth
        if change.from_state == "INVESTIGATE" and change.to_state == "RECOMMEND"
    )

    assert "Business quality could be measured again (80)" in recovered.moved


def test_no_recorded_change_is_ever_worded_as_a_fall_when_it_was_unmeasurable() -> None:
    """The distinction the whole slice turns on, over the whole journal.

    A score that stopped being measurable is a fact about this platform's
    reading. Wording it as a fall would report a provider outage as a
    worse business, on every security at once.
    """

    for symbol in ("VOW3.DE", "MSFT", "DIS", "BTC"):
        for change in committed(symbol).course().transitions:
            for line in change.moved:
                if "could no longer be measured" in line:
                    assert "fell" not in line
                    assert "→" not in line


def test_a_stability_claim_never_covers_a_window_containing_a_change() -> None:
    """Acceptance 2, over every symbol the journal holds.

    "Stable — N consecutive reviews since DATE" is arithmetically true of
    a run and false as a period whenever the record changed before it.
    Where the case ever changed, the sentence counts the changes instead
    of dating the calm.
    """

    assert list(COMMITTED_EVENTS.glob("*.json")), (
        "the committed decision records are this test's evidence and are missing"
    )

    for symbol in ("VOW3.DE", "MSFT", "DIS", "JPM", "AAPL", "BTC"):
        recorded = committed(symbol)
        state = recorded.current_state

        if state is None:
            continue

        trend = recorded.trend_against(state)

        assert trend is not None

        if recorded.state_changes:
            assert "Stable — " not in trend.stated
            assert f"changed {recorded.state_changes} time" in trend.stated
        else:
            assert trend.stated.startswith("Stable — ")


# ── the states, on records this test builds itself ──────────────────


def test_a_first_review_is_an_absence_and_never_a_trend() -> None:
    """Acceptance 3. A first review has nothing before it to differ from."""

    course = history(record(DecisionState.PREPARE, 60)).course()

    assert course.reviews == 1
    assert course.changes == 0
    assert course.transitions == ()
    assert course.absent_because is not None
    assert "A first review has nothing before it" in course.absent_because
    assert course.stated == ""


def test_nothing_recorded_is_its_own_absence() -> None:
    course = DecisionHistory(symbol="EXAM").course()

    assert course.reviews == 0
    assert course.absent_because is not None
    assert "no decision about this security yet" in course.absent_because


def test_an_unchanged_decision_says_so_rather_than_showing_nothing() -> None:
    course = history(
        record(DecisionState.PREPARE, 60),
        record(DecisionState.PREPARE, 61, day=1),
    ).course()

    assert course.changes == 0
    assert course.transitions == ()
    assert "has not changed" in course.stated
    assert course.absent_because is None


def test_a_whole_missing_score_set_is_one_silence_and_never_five_findings() -> None:
    """An earlier decision recorded before the journal kept scores says
    that once. Enumerating it as five scores "measured again" would turn
    a single absence into a list of findings."""

    course = history(
        record(DecisionState.INVESTIGATE, 60),
        record(
            DecisionState.PREPARE,
            70,
            day=1,
            scores=RecordedScores(quality=80, evidence=70),
        ),
    ).course()

    change = course.transitions[0]

    assert change.unexplained
    assert change.moved == ()


def test_a_score_that_stopped_being_measurable_is_not_a_score_that_fell() -> None:
    course = history(
        record(
            DecisionState.RECOMMEND,
            80,
            scores=RecordedScores(quality=62, evidence=87),
        ),
        record(
            DecisionState.INVESTIGATE,
            70,
            day=1,
            scores=RecordedScores(quality=None, evidence=77),
        ),
    ).course()

    change = course.transitions[0]

    assert not change.unexplained
    assert "Business quality could no longer be measured (it was 62)" in change.moved
    assert "Evidence strength fell, 87 → 77" in change.moved

    # Never a zero, and never a deterioration.
    assert not any("0" == line.strip() for line in change.moved)
    assert not any("quality fell" in line for line in change.moved)


def test_the_rationale_travels_verbatim() -> None:
    """The sentence the CIO recorded then, never one composed now."""

    said = "Business quality has not been measured, so the case cannot progress."

    course = history(
        record(DecisionState.RECOMMEND, 80),
        record(DecisionState.INVESTIGATE, 70, day=1, rationale=said),
    ).course()

    assert course.transitions[0].rationale == said


def test_the_scores_are_named_the_way_this_dossier_names_them() -> None:
    """A token's quality moving is an asset-quality move.

    The keys are the record's and never vary; only the words do — the
    same contract `conviction_change_against` already takes.
    """

    from app.domain.asset_class import AssetClass

    course = history(
        record(DecisionState.PREPARE, 60, scores=RecordedScores(quality=40)),
        record(DecisionState.RECOMMEND, 70, day=1, scores=RecordedScores(quality=80)),
    ).course(score_labels_for(AssetClass.CRYPTO))

    assert "Asset quality improved, 40 → 80" in course.transitions[0].moved


def test_the_most_recent_change_is_read_first() -> None:
    course = history(
        record(DecisionState.INVESTIGATE, 60, scores=RecordedScores(quality=40)),
        record(DecisionState.PREPARE, 70, day=1, scores=RecordedScores(quality=50)),
        record(DecisionState.RECOMMEND, 80, day=2, scores=RecordedScores(quality=60)),
    ).course()

    assert [change.to_state for change in course.transitions] == [
        DecisionState.RECOMMEND.value,
        DecisionState.PREPARE.value,
    ]


def test_a_run_that_is_the_whole_record_still_dates_its_calm() -> None:
    """Where the case never changed, "since" is honest and is kept."""

    recorded = history(
        record(DecisionState.PREPARE, 60),
        record(DecisionState.PREPARE, 60, day=1),
    )

    trend = recorded.trend_against(DecisionState.PREPARE)

    assert trend is not None
    assert trend.stated.startswith("Stable — 3 consecutive reviews since ")


# ── at the wire, and neutral to the decision ────────────────────────


def test_the_dossier_serves_the_course_with_its_sentences() -> None:
    """The shape a surface renders: states declared, sentences present.

    The fixture brain records no history, so this is the honest empty
    state — which is the one a surface is most likely to get wrong.
    """

    from fastapi.testclient import TestClient

    from app.api.dependencies import get_brain_builder_service
    from app.api.main import app
    from tests.test_api_routes import StubBrainBuilder, make_brain

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    try:
        with TestClient(app) as client:
            body = client.get("/executive/MSFT/dossier").json()
    finally:
        app.dependency_overrides.clear()

    course = body["decision_course"]

    assert course is not None
    assert course["reviews"] == 0
    assert course["changes"] == 0
    assert course["transitions"] == []
    assert course["absent_because"]
    assert "no decision about this security yet" in course["absent_because"]


def test_the_recorded_course_cannot_move_the_decision(monkeypatch) -> None:
    """The boundary: this section reports history and decides nothing.

    Two dossiers over an identical brain — one whose journal holds a
    flap, one whose journal holds nothing. The course differs; every
    decision field is byte-identical.
    """

    from typing import cast

    from fastapi.testclient import TestClient

    from app.api.dependencies import get_brain_builder_service
    from app.api.main import app
    from app.brain.brain import Brain
    from tests.test_api_routes import StubBrainBuilder, make_brain

    flap = history(
        record(
            DecisionState.RECOMMEND,
            80,
            scores=RecordedScores(quality=62, evidence=87),
        ),
        record(
            DecisionState.INVESTIGATE,
            70,
            day=1,
            scores=RecordedScores(quality=None, evidence=77),
        ),
    )

    app.dependency_overrides[get_brain_builder_service] = lambda: StubBrainBuilder(
        make_brain()
    )

    def capture() -> dict[str, object]:
        with TestClient(app) as client:
            return cast(dict[str, object], client.get("/executive/MSFT/dossier").json())

    try:
        without = capture()

        monkeypatch.setattr(
            Brain,
            "decision_history_for",
            lambda self, symbol: DecisionHistory(symbol=symbol, records=flap.records),
        )

        with_history = capture()
    finally:
        app.dependency_overrides.clear()

    # The course genuinely changed between the two requests…
    assert cast(dict[str, object], without["decision_course"])["changes"] == 0
    assert cast(dict[str, object], with_history["decision_course"])["changes"] == 1

    # …and the decision did not, field by field. `trend` and
    # `conviction_change` are deliberately excluded: they are readings of
    # the same recorded history and are *expected* to move with it.
    for field in (
        "decision_state",
        "conviction",
        "conviction_label",
        "committee_agreement",
        "rationale",
        "action",
        "playbook",
        "classification",
        "summary",
        "expected_holding_period",
        "catalysts",
        "invalidation_conditions",
        "next_trigger",
        "security_evidenced",
        "evidence_weighed",
        "strengths",
        "risks",
        "missing_evidence",
        "scores",
        "context_strengths",
        "context_risks",
        "committees",
    ):
        assert without[field] == with_history[field], field
