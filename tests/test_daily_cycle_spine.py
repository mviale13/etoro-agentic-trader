"""The Daily CIO cycle spine: identity, order, honesty.

#217 measured the absences the spine fills; the owner's amendment
sharpened four truths this file now pins: the course travels with the
disposition (`workspace.action`, carried, never re-inferred); the first
cycle is an initial baseline, not a quiet day; an incomplete stream
refuses the comparison instead of decorating it; and a lifecycle
anomaly is counted, never pooled. Plus one hygiene rule: an exception's
own text never reaches the durable record.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace

from app.application.learning.decision_journal import DecisionJournal
from app.commands.cycle import new_cycle_id, render, run
from app.domain.daily_cycle import (
    NO_ACTION,
    ComparisonBasis,
    ComparisonOutcome,
    CycleFinished,
    CycleLog,
    CycleStage,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
    StageOutcome,
    movement,
    no_action_permitted,
)
from app.domain.executive.executive_action import ActionKind
from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore

MOMENT = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)


# ── fakes: the two stages, controllable ─────────────────────────────


class AcquisitionStub:
    """The market read, with a spy on when it was asked."""

    def __init__(self, store: DailyCycleStore, fail: bool = False) -> None:
        self._store = store
        self._fail = fail
        self.started_seen_on_disk: bool | None = None

    async def acquire(self):
        # Acceptance 1: at the moment acquisition begins, STARTED must
        # already be durable — read the store's own file to prove it.
        self.started_seen_on_disk = self._store.path.exists() and any(
            '"kind": "started"' in line
            for line in self._store.path.read_text().splitlines()
        )

        if self._fail:
            raise RuntimeError(
                "GET https://broker.invalid/pnl?account=ACCT-99&key=sk-FAKE-123"
            )

        return SimpleNamespace(
            securities=(
                SimpleNamespace(symbol="KO", priced=True),
                SimpleNamespace(symbol="HYPE", priced=False),
            ),
            priced=("KO",),
        )


def decision(
    symbol: str,
    state: str,
    rationale: str = "held basis",
    kind: ActionKind = ActionKind.HOLD,
    statement: str = "Keep the position as it is.",
) -> object:
    """One workspace-shaped pair: the decision and its pipeline course."""

    return SimpleNamespace(
        decision=SimpleNamespace(
            symbol=symbol,
            state=SimpleNamespace(value=state),
            rationale=rationale,
            conviction=60,
            evidence_as_of=None,
        ),
        action=SimpleNamespace(
            kind=kind,
            statement=statement,
            because=rationale,
        ),
    )


class BrainStub:
    async def build(self):
        return SimpleNamespace()


class BriefingStub:
    def __init__(self, *workspaces, fail: bool = False) -> None:
        self._workspaces = workspaces
        self._fail = fail

    def build(self, brain):
        if self._fail:
            raise RuntimeError(
                "pipeline exploded at https://internal.invalid?token=sk-FAKE-456"
            )

        return SimpleNamespace(workspaces=self._workspaces)


def cycle_run(
    tmp_path,
    *workspaces,
    fail_acquisition: bool = False,
    fail_decisions: bool = False,
) -> tuple[int, DailyCycleStore, AcquisitionStub]:
    store = DailyCycleStore(tmp_path / "cycles")
    acquisition = AcquisitionStub(store, fail=fail_acquisition)

    code = asyncio.run(
        run(
            store=store,
            acquisition=acquisition,
            brains=BrainStub(),
            briefings=BriefingStub(*workspaces, fail=fail_decisions),
        )
    )

    return code, store, acquisition


# ── the lifecycle (acceptance 1–2, 6, 9) ────────────────────────────


def test_started_is_durable_before_acquisition_begins(tmp_path, capsys) -> None:
    _, _, acquisition = cycle_run(tmp_path, decision("KO", "PREPARE"))

    assert acquisition.started_seen_on_disk is True


def test_a_successful_run_is_one_started_and_one_complete_terminal(
    tmp_path, capsys
) -> None:
    code, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))

    log = store.log()

    assert code == 0
    assert len(log.records) == 1
    assert log.records[0].finished is not None
    assert log.records[0].finished.status is CycleStatus.COMPLETE
    assert not log.records[0].is_interrupted


def test_a_dangling_started_renders_as_interrupted(tmp_path) -> None:
    store = DailyCycleStore(tmp_path / "cycles")

    store.append_started(CycleStarted(cycle_id="abc123", started_at=MOMENT))

    log = store.log()

    assert log.records[0].is_interrupted

    rendered = render(log.records[0], CycleLog())

    assert "interrupted" in rendered
    assert "COMPLETE" not in rendered
    assert "FAILED" not in rendered
    assert "PARTIAL" not in rendered
    assert "changed" not in rendered.casefold()
    assert NO_ACTION not in rendered


def test_the_next_run_discloses_the_previous_interruption(tmp_path, capsys) -> None:
    store = DailyCycleStore(tmp_path / "cycles")
    store.append_started(CycleStarted(cycle_id="dead00beef00", started_at=MOMENT))

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "PREPARE")),
        )
    )

    rendered = capsys.readouterr().out

    assert "dead00beef00" in rendered
    assert "recorded no end" in rendered
    assert "interrupted" in rendered


def test_a_second_run_receives_a_distinct_cycle_id(tmp_path, capsys) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "PREPARE")),
        )
    )

    log = store.log()

    assert len(log.records) == 2
    assert log.records[0].cycle_id != log.records[1].cycle_id
    assert new_cycle_id() != new_cycle_id()


# ── demonstration 1: the initial baseline ───────────────────────────


def test_the_first_cycle_is_an_initial_baseline_and_shows_its_courses(
    tmp_path, capsys
) -> None:
    """A first cycle has nothing to have changed from, and says so.

    It reports the baseline, displays the courses the canonical
    pipeline produced — an OPEN course included — and claims neither a
    previous comparison nor a quiet day.
    """

    _, store, _ = cycle_run(
        tmp_path,
        decision(
            "KO",
            "RECOMMEND",
            "quality banded",
            kind=ActionKind.OPEN,
            statement="Consider opening a position.",
        ),
    )

    finished = store.log().records[0].finished

    assert finished is not None
    assert finished.comparison.outcome is ComparisonOutcome.INITIAL_BASELINE
    assert finished.newly_produced == ()
    assert finished.changed == ()
    assert finished.unchanged == ()

    rendered = capsys.readouterr().out

    assert (
        "Initial cycle recorded; no previous completed cycle exists for "
        "change comparison." in rendered
    )
    assert "KO: RECOMMEND — Consider opening a position. (open)" in rendered
    assert "No recommendation changed" not in rendered
    assert "nothing changed" not in rendered.casefold()
    assert NO_ACTION not in rendered


# ── demonstration 2: a newly produced actionable course ─────────────


def test_a_new_actionable_security_reaches_attention_with_its_course(
    tmp_path, capsys
) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(
                decision("KO", "PREPARE"),
                decision(
                    "DIS",
                    "RECOMMEND",
                    "case satisfied",
                    kind=ActionKind.OPEN,
                    statement="Consider opening a position.",
                ),
            ),
        )
    )

    finished = store.log().records[1].finished
    rendered = capsys.readouterr().out

    assert finished is not None
    assert finished.comparison.outcome is ComparisonOutcome.COMPARED
    assert finished.newly_produced == ("DIS",)
    assert any(
        "DIS: Consider opening a position. (open)" in a for a in finished.attention
    )
    assert "Newly considered:" in rendered
    assert "DIS — Consider opening a position. (open)" in rendered
    assert NO_ACTION not in rendered


def test_a_new_non_actionable_course_is_newly_considered_not_an_action(
    tmp_path, capsys
) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(
                decision("KO", "PREPARE"),
                decision(
                    "AZN",
                    "INVESTIGATE",
                    kind=ActionKind.WATCH,
                    statement="Nothing to do yet.",
                ),
            ),
        )
    )

    finished = store.log().records[1].finished
    rendered = capsys.readouterr().out

    assert finished is not None
    assert finished.newly_produced == ("AZN",)
    assert not any("AZN" in item for item in finished.attention)
    assert "AZN (INVESTIGATE; its course asks for nothing yet)" in rendered


# ── demonstration 3: PARTIAL never reads quiet ──────────────────────


def test_partial_reports_the_failed_stage_and_never_no_action(tmp_path, capsys) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store, fail=True),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "PREPARE")),
        )
    )

    finished = store.log().records[1].finished
    rendered = capsys.readouterr().out

    assert finished is not None
    assert finished.status is CycleStatus.PARTIAL
    assert finished.changed == ()
    assert any("acquisition stage failed" in item for item in finished.attention)
    assert "the acquisition stage failed (RuntimeError)" in rendered
    assert NO_ACTION not in rendered


# ── demonstration 4: the one quiet shape ────────────────────────────


def test_no_action_is_said_exactly_and_only_in_the_one_permitted_shape(
    tmp_path, capsys
) -> None:
    """COMPLETE + valid prior comparison + nothing changed + no asking
    course + no refusal + no failed stage — and only that."""

    store = DailyCycleStore(tmp_path / "cycles")

    class CleanAcquisition:
        async def acquire(self):
            return SimpleNamespace(
                securities=(SimpleNamespace(symbol="KO", priced=True),),
                priced=("KO",),
            )

    for _ in range(2):
        asyncio.run(
            run(
                store=store,
                acquisition=CleanAcquisition(),
                brains=BrainStub(),
                briefings=BriefingStub(decision("KO", "PREPARE")),
            )
        )

    rendered = capsys.readouterr().out
    finished = store.log().records[1].finished

    assert finished is not None
    assert finished.status is CycleStatus.COMPLETE
    assert finished.comparison.outcome is ComparisonOutcome.COMPARED
    assert no_action_permitted(finished)
    assert NO_ACTION in rendered
    assert "No recommendation changed against the previous cycle." in rendered


def test_refusals_forbid_no_action_even_on_a_complete_cycle(tmp_path, capsys) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    # Second run: HYPE unpriced again — COMPLETE, compared, unchanged,
    # and still not a quiet day.
    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "PREPARE")),
        )
    )

    finished = store.log().records[1].finished
    rendered = capsys.readouterr().out

    assert finished is not None
    assert finished.status is CycleStatus.COMPLETE
    assert finished.refusals == ("HYPE: no price came back",)
    assert not no_action_permitted(finished)
    assert NO_ACTION not in rendered
    assert "says nothing about the business itself" in rendered


# ── demonstration 5: incomplete history refuses movement ────────────


def test_an_unreadable_line_between_cycles_refuses_the_comparison(
    tmp_path, capsys
) -> None:
    """A disclosure beside a derived change does not make it safe.

    The unreadable record may be the actual previous cycle, so the
    comparison is refused, nothing is classified, and the day is
    unclassified rather than quiet.
    """

    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write('{"schema": 9, "kind": "finished", "cycle_id": "future"}\n')

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "RECOMMEND", "moved")),
        )
    )

    finished = store.log().records[1].finished
    rendered = capsys.readouterr().out

    assert finished is not None
    assert finished.comparison.outcome is ComparisonOutcome.REFUSED
    assert "incomplete" in finished.comparison.because
    assert finished.changed == ()
    assert finished.unchanged == ()
    assert finished.newly_produced == ()
    assert "Change comparison refused" in rendered
    assert "No recommendation changed" not in rendered
    assert NO_ACTION not in rendered
    # The present is still recorded and shown.
    assert finished.decisions[0].symbol == "KO"
    assert "Current courses" in rendered


# ── demonstration 6: lifecycle anomalies ────────────────────────────


def test_every_lifecycle_anomaly_is_counted_and_never_pooled(tmp_path) -> None:
    store = DailyCycleStore(tmp_path / "cycles")

    finished_line = {
        "schema": 1,
        "kind": "finished",
        "cycle_id": "c1",
        "at": MOMENT.isoformat(),
        "status": "complete",
        "stages": [],
        "comparison": {"outcome": "initial_baseline"},
    }

    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.touch()

    # Terminal before start, then the start, then a duplicate start,
    # then two finishes — one valid pairing at most, three anomalies…
    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(finished_line) + "\n")  # terminal-before-start

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))  # dup

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(finished_line) + "\n")  # the valid pairing
        handle.write(json.dumps(finished_line) + "\n")  # duplicate finished

    # …plus an orphan FINISHED for a cycle that never started.
    orphan = dict(finished_line, cycle_id="ghost")

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(orphan) + "\n")

    log = store.log()

    assert len(log.records) == 1, "one valid lifecycle survives"
    assert log.lifecycle_anomalies == 4
    assert not log.is_complete_stream


def test_a_byte_identical_duplicate_is_still_a_second_event(tmp_path) -> None:
    store = DailyCycleStore(tmp_path / "cycles")

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))

    line = store.path.read_text().strip()

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")

    log = store.log()

    assert log.lifecycle_anomalies == 1
    assert not log.is_complete_stream


# ── demonstration 7: no secret reaches the record ───────────────────


def test_stage_failures_persist_no_url_account_or_key(tmp_path, capsys) -> None:
    """The exception's own text never reaches the store or the render."""

    cycle_run(
        tmp_path,
        decision("KO", "PREPARE"),
        fail_acquisition=True,
    )

    store = DailyCycleStore(tmp_path / "cycles")
    stored = store.path.read_text()
    rendered = capsys.readouterr().out

    for leaked in ("broker.invalid", "ACCT-99", "sk-FAKE-123", "https://"):
        assert leaked not in stored
        assert leaked not in rendered

    finished = store.log().records[0].finished

    assert finished is not None
    assert any(
        stage.because == "the acquisition stage failed (RuntimeError)"
        for stage in finished.stages
    )


def test_a_failed_decision_pass_also_leaks_nothing(tmp_path, capsys) -> None:
    code, store, _ = cycle_run(tmp_path, fail_decisions=True)
    stored = store.path.read_text()
    rendered = capsys.readouterr().out

    assert code == 1
    for leaked in ("internal.invalid", "sk-FAKE-456", "https://"):
        assert leaked not in stored
        assert leaked not in rendered

    assert "failed cycle, not a quiet one" in rendered
    assert "No recommendation changed" not in rendered
    assert NO_ACTION not in rendered


# ── demonstration 8: the course comes from workspace.action ────────


def test_the_production_summary_is_built_from_workspace_action() -> None:
    """Pinned on the source, so no injected seam can bypass it.

    The AST of the command's DecisionSummary construction must source
    every action field from `workspace.action`, and no actionability
    may be re-inferred from a state string.
    """

    import ast
    import pathlib

    tree = ast.parse(pathlib.Path("app/commands/cycle.py").read_text())

    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "DecisionSummary"
    ]

    assert len(calls) == 1, "one production construction"

    keywords = {kw.arg: ast.dump(kw.value) for kw in calls[0].keywords}

    for field in ("action_kind", "action_statement", "action_because"):
        assert field in keywords
        assert "attr='action'" in keywords[field], (
            f"{field} must come from workspace.action"
        )

    assert "asks_for_something" in keywords
    assert "attr='asks_for_something'" in keywords["asks_for_something"], (
        "actionability is the ActionKind's own property, never re-inferred"
    )

    source = pathlib.Path("app/commands/cycle.py").read_text()

    for reinfer in ('== "RECOMMEND"', "state in (", "RECOMMEND,"):
        assert reinfer not in source, "no actionability from state strings"


def test_the_stored_summary_round_trips_the_course(tmp_path, capsys) -> None:
    _, store, _ = cycle_run(
        tmp_path,
        decision(
            "KO",
            "RECOMMEND",
            kind=ActionKind.OPEN,
            statement="Consider opening a position.",
        ),
    )

    entry = store.log().records[0].finished.decisions[0]  # type: ignore[union-attr]

    assert entry.action_kind == "open"
    assert entry.action_statement == "Consider opening a position."
    assert entry.asks_for_something is True


# ── demonstration 9 and the journal stamp (acceptance 7, 11) ────────


def test_cycle_decision_entries_all_carry_the_cycle_id() -> None:
    saved = []

    class Repository:
        def save(self, event) -> None:
            saved.append(event)

        def load(self, day):
            return []

        def load_all(self):
            return []

    real = SimpleNamespace(
        symbol="KO",
        state=SimpleNamespace(value="PREPARE"),
        conviction=60,
        rationale="held basis",
        decided_under=(),
        evidence_records=(),
        decided_at=MOMENT,
    )

    DecisionJournal(Repository(), cycle_id="cycle0001").record(real)  # type: ignore[arg-type]
    DecisionJournal(Repository()).record(real)  # type: ignore[arg-type]

    tagged, untagged = saved

    assert tagged.payload["cycle_id"] == "cycle0001"
    assert "cycle_id" not in untagged.payload

    without_stamp = {k: v for k, v in tagged.payload.items() if k != "cycle_id"}

    assert without_stamp == untagged.payload


def test_the_cycle_carries_judgment_and_never_reinterprets_it() -> None:
    """The command consumes workspace fields; it imports neither the
    decision engine nor the action builder, so identical inputs keep
    identical outputs by construction."""

    import ast
    import pathlib

    tree = ast.parse(pathlib.Path("app/commands/cycle.py").read_text())

    imports = [
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    ]

    for forbidden in (
        "app.cio",
        "app.application.executive.executive_action_builder",
        "app.application.executive.decision_evidence_builder",
    ):
        assert not any(module.startswith(forbidden) for module in imports), forbidden


def test_untagged_page_view_entries_never_create_a_cycle_change() -> None:
    previous = CycleFinished(
        cycle_id="prev00000001",
        finished_at=MOMENT,
        status=CycleStatus.COMPLETE,
        stages=(CycleStage(name="decisions", outcome=StageOutcome.RAN),),
        comparison=ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE),
        decisions=(DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),),
    )

    current = (DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),)

    produced, changed, unchanged = movement(current, previous)

    assert changed == ()
    assert unchanged == ("KO",)

    moved = (DecisionSummary(symbol="KO", state="RECOMMEND", rationale="r2"),)

    assert movement(moved, previous)[1] == ("KO",)


# ── what this slice must not introduce (acceptance 12) ──────────────


def test_the_cycle_module_reaches_no_forbidden_path() -> None:
    import ast
    import pathlib

    forbidden = (
        "anthropic",
        "openai",
        "massive",
        "personal_news",
        "edgar",
        "leadership",
        "smtp",
        "notification",
        "webhook",
    )

    for module in (
        "app/commands/cycle.py",
        "app/domain/daily_cycle.py",
        "app/infrastructure/evidence/daily_cycle_store.py",
    ):
        tree = ast.parse(pathlib.Path(module).read_text())

        imports = [
            name.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for name in node.names
        ] + [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        ]

        for imported in imports:
            assert not any(bad in imported.casefold() for bad in forbidden), (
                f"{module} imports {imported}"
            )


def test_the_render_vocabulary_keeps_the_standing_rules(tmp_path, capsys) -> None:
    cycle_run(tmp_path, decision("KO", "PREPARE"))

    rendered = capsys.readouterr().out.casefold()

    for banned in ("resolved", "corrected", "weak business", "poor quality"):
        assert banned not in rendered


def test_the_store_lives_under_the_evidence_root(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MOVRVEST_EVIDENCE_ROOT", str(tmp_path))

    store = DailyCycleStore()

    assert str(store.path).startswith(str(tmp_path))


# ── final contract pins: no silent drops ────────────────────────────


def test_no_security_disappears_when_its_pass_is_incomplete(tmp_path, capsys) -> None:
    """One carried, two refused in words — three symbols, all accounted.

    A workspace whose canonical pass produced no disposition or no
    course is a per-security refusal inside a COMPLETE cycle, named for
    which half was missing — never a silent drop, never a manufactured
    action, and never a PARTIAL merely because one security refused.
    """

    broken_no_action = SimpleNamespace(
        symbol="AZN",
        decision=SimpleNamespace(
            symbol="AZN",
            state=SimpleNamespace(value="PREPARE"),
            rationale="r",
            conviction=50,
            evidence_as_of=None,
        ),
        action=None,
    )
    broken_no_decision = SimpleNamespace(symbol="CYD", decision=None, action=None)

    _, store, _ = cycle_run(
        tmp_path,
        decision("KO", "PREPARE"),
        broken_no_action,
        broken_no_decision,
    )

    finished = store.log().records[0].finished
    rendered = capsys.readouterr().out

    assert finished is not None
    assert finished.status is CycleStatus.COMPLETE, (
        "one refused security does not degrade execution status"
    )
    assert [entry.symbol for entry in finished.decisions] == ["KO"]

    course_missing = next(r for r in finished.refusals if r.startswith("AZN"))
    disposition_missing = next(r for r in finished.refusals if r.startswith("CYD"))

    assert "a disposition and no course" in course_missing
    assert "no disposition" in disposition_missing

    for refusal in (course_missing, disposition_missing):
        assert "constrains what the cycle can say" in refusal
        assert "says nothing about the business" in refusal
        assert refusal in finished.attention
        assert refusal in rendered

    assert NO_ACTION not in rendered


def test_no_useful_pair_for_any_security_is_failed(tmp_path, capsys) -> None:
    """Every workspace defective: no useful decision pass at all."""

    code, store, _ = cycle_run(
        tmp_path,
        SimpleNamespace(symbol="AZN", decision=None, action=None),
    )

    finished = store.log().records[0].finished

    assert code == 1
    assert finished is not None
    assert finished.status is CycleStatus.FAILED
    assert any("AZN" in refusal for refusal in finished.refusals), (
        "the refused security is still accounted for in the terminal record"
    )


# ── final contract pins: three separate defect counts ───────────────


def test_the_three_stream_defects_are_counted_separately(tmp_path) -> None:
    """One unreadable, one unsupported, one anomaly — exactly 1 / 1 / 1.

    Unknown-schema JSON is not unreadable; malformed JSON is; a decoded
    but invalid two-event lifecycle is an anomaly. Collapsing any two
    would let one defect class hide inside another's count.
    """

    store = DailyCycleStore(tmp_path / "cycles")

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))  # anomaly

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write("{malformed json\n")  # unreadable
        handle.write(
            '{"schema": 9, "kind": "started", "cycle_id": "x"}\n'
        )  # unsupported

    log = store.log()

    assert log.unreadable_records == 1
    assert log.unsupported_schemas == 1
    assert log.lifecycle_anomalies == 1
    assert not log.is_complete_stream


def test_the_refusal_reason_names_the_individual_counts(tmp_path, capsys) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write("{malformed\n")

    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "PREPARE")),
        )
    )

    finished = store.log().records[1].finished

    assert finished is not None
    assert finished.comparison.outcome is ComparisonOutcome.REFUSED
    assert "1 unreadable record(s)" in finished.comparison.because
    assert "0 unsupported-schema record(s)" in finished.comparison.because
    assert "0 lifecycle anomaly(ies)" in finished.comparison.because


# ── final contract pins: comparison-basis invariants ────────────────


def test_every_contradictory_basis_shape_is_unconstructable() -> None:
    """Each outcome permits exactly one field pattern; whitespace is empty."""

    import pytest

    # Valid shapes construct.
    ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE)
    ComparisonBasis(outcome=ComparisonOutcome.COMPARED, prior_cycle_id="prev1")
    ComparisonBasis(outcome=ComparisonOutcome.REFUSED, because="stream incomplete")

    invalid = [
        # INITIAL_BASELINE with anything filled.
        dict(outcome=ComparisonOutcome.INITIAL_BASELINE, prior_cycle_id="p"),
        dict(outcome=ComparisonOutcome.INITIAL_BASELINE, because="r"),
        # COMPARED without a prior, or with a reason.
        dict(outcome=ComparisonOutcome.COMPARED),
        dict(outcome=ComparisonOutcome.COMPARED, prior_cycle_id="   "),
        dict(outcome=ComparisonOutcome.COMPARED, prior_cycle_id="p", because="r"),
        # REFUSED without a reason, or with a prior.
        dict(outcome=ComparisonOutcome.REFUSED),
        dict(outcome=ComparisonOutcome.REFUSED, because="   "),
        dict(outcome=ComparisonOutcome.REFUSED, because="r", prior_cycle_id="p"),
    ]

    for fields in invalid:
        with pytest.raises(ValueError):
            ComparisonBasis(**fields)


def test_a_stored_contradictory_basis_makes_the_record_unreadable(
    tmp_path,
) -> None:
    """It decodes into no lifecycle and participates in no movement."""

    store = DailyCycleStore(tmp_path / "cycles")

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))

    corrupt = {
        "schema": 1,
        "kind": "finished",
        "cycle_id": "c1",
        "at": MOMENT.isoformat(),
        "status": "complete",
        "stages": [],
        "comparison": {"outcome": "compared", "prior_cycle_id": "  "},
        "decisions": [{"symbol": "KO", "state": "RECOMMEND", "rationale": "r"}],
    }

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(corrupt) + "\n")

    log = store.log()

    assert log.unreadable_records == 1
    assert not log.is_complete_stream
    assert log.records[0].is_interrupted, (
        "the invalid terminal paired with nothing — the cycle stays dangling"
    )
    assert log.latest_terminal() is None, "no movement can rest on it"
