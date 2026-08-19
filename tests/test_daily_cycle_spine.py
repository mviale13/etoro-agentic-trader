"""The Daily CIO cycle spine: identity, order, honesty.

#217 measured the absences this slice fills: no cycle identity existed,
so "nothing changed" and "the cycle failed" were indistinguishable; and
decisions entered the journal by page views, so change detection was a
fact about page traffic. Every case below pins one of the fifteen
acceptance requirements of the owner's ruling — or pins that nothing
else moved.
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
    CycleFinished,
    CycleLog,
    CycleRecord,
    CycleStage,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
    StageOutcome,
    movement,
)
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
            raise RuntimeError("the broker did not answer")

        return SimpleNamespace(
            securities=(
                SimpleNamespace(symbol="KO", priced=True),
                SimpleNamespace(symbol="HYPE", priced=False),
            ),
            priced=("KO",),
        )


def decision(symbol: str, state: str, rationale: str = "held basis") -> object:
    return SimpleNamespace(
        symbol=symbol,
        state=SimpleNamespace(value=state),
        rationale=rationale,
        conviction=60,
        evidence_as_of=None,
    )


class BrainStub:
    async def build(self):
        return SimpleNamespace()


class BriefingStub:
    def __init__(self, *decisions, fail: bool = False) -> None:
        self._decisions = decisions
        self._fail = fail

    def build(self, brain):
        if self._fail:
            raise RuntimeError("the pipeline could not run")

        return SimpleNamespace(
            workspaces=tuple(
                SimpleNamespace(decision=entry) for entry in self._decisions
            )
        )


def cycle_run(
    tmp_path,
    *decisions_,
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
            briefings=BriefingStub(*decisions_, fail=fail_decisions),
        )
    )

    return code, store, acquisition


# ── 1–2: the lifecycle ──────────────────────────────────────────────


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


# ── 3: refusals coexist with COMPLETE ───────────────────────────────


def test_item_level_refusals_coexist_with_complete(tmp_path, capsys) -> None:
    """Execution status and evidence sufficiency are separate dimensions."""

    code, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))

    finished = store.log().records[0].finished

    assert finished is not None
    assert finished.status is CycleStatus.COMPLETE
    assert finished.refusals == ("HYPE: no price came back",)
    assert finished.securities_priced == 1
    assert finished.securities_asked == 2

    rendered = capsys.readouterr().out

    assert "COMPLETE" in rendered
    assert "HYPE: no price came back" in rendered
    # A gap is a fact about the evidence, never about the business.
    assert "says nothing about the business itself" in rendered


# ── 4–5: PARTIAL and FAILED ─────────────────────────────────────────


def test_a_failed_stage_with_a_useful_decision_pass_is_partial(
    tmp_path, capsys
) -> None:
    code, store, _ = cycle_run(
        tmp_path, decision("KO", "PREPARE"), fail_acquisition=True
    )

    finished = store.log().records[0].finished

    assert code == 0
    assert finished is not None
    assert finished.status is CycleStatus.PARTIAL
    assert any(
        stage.name == "acquisition"
        and stage.outcome is StageOutcome.FAILED
        and "did not answer" in stage.because
        for stage in finished.stages
    )


def test_no_useful_decision_pass_is_failed(tmp_path, capsys) -> None:
    code, store, _ = cycle_run(tmp_path, fail_decisions=True)

    finished = store.log().records[0].finished

    assert code == 1
    assert finished is not None
    assert finished.status is CycleStatus.FAILED

    rendered = capsys.readouterr().out

    # Acceptance 10, the failing half: a failed cycle never reads as a
    # quiet one.
    assert "failed cycle, not a quiet one" in rendered
    assert "No recommendation changed" not in rendered
    assert NO_ACTION not in rendered


# ── 6: the dangling STARTED ─────────────────────────────────────────


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


# ── 7–8: tagging, and isolation from page traffic ───────────────────


def test_cycle_decision_entries_all_carry_the_cycle_id() -> None:
    """The journal stamp: present with a cycle, absent without one."""

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

    # Acceptance 11's journal half: the only difference the stamp makes
    # is the stamp — every recorded fact is byte-identical beside it.
    without_stamp = {k: v for k, v in tagged.payload.items() if k != "cycle_id"}

    assert without_stamp == untagged.payload


def test_untagged_page_view_entries_never_create_a_cycle_change(tmp_path) -> None:
    """Movement is derived from cycle records only, by construction.

    A page view writes a journal event and no cycle event, so it cannot
    reach `movement` at all — the comparison base is the previous
    cycle's own terminal record.
    """

    previous = CycleFinished(
        cycle_id="prev00000001",
        finished_at=MOMENT,
        status=CycleStatus.COMPLETE,
        stages=(CycleStage(name="decisions", outcome=StageOutcome.RAN),),
        decisions=(DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),),
    )

    current = (DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),)

    produced, changed, unchanged = movement(current, previous)

    assert changed == ()
    assert unchanged == ("KO",)

    # And a real state move is a change, with nothing else consulted.
    moved = (DecisionSummary(symbol="KO", state="RECOMMEND", rationale="r2"),)

    assert movement(moved, previous)[1] == ("KO",)


def test_the_first_cycle_claims_no_changes(tmp_path) -> None:
    current = (DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),)

    produced, changed, unchanged = movement(current, None)

    assert produced == ("KO",)
    assert changed == ()
    assert unchanged == ()


# ── 9: distinct cycle ids ───────────────────────────────────────────


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


# ── 10: "no changes" vs FAILED vs interrupted ───────────────────────


def test_no_changes_is_its_own_state_and_never_a_failure_reading(
    tmp_path, capsys
) -> None:
    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))
    capsys.readouterr()

    # Second cycle, same decision: completed, nothing changed.
    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "PREPARE")),
        )
    )

    rendered = capsys.readouterr().out

    assert "COMPLETE" in rendered
    assert "No recommendation changed against the previous cycle." in rendered
    assert "failed" not in rendered.casefold().replace("no price came back", "")

    # And with a change, the contemporaneous rationale rides along.
    asyncio.run(
        run(
            store=store,
            acquisition=AcquisitionStub(store),
            brains=BrainStub(),
            briefings=BriefingStub(decision("KO", "RECOMMEND", "quality banded")),
        )
    )

    changed = capsys.readouterr().out

    assert "KO: now RECOMMEND — quality banded" in changed


def test_no_action_is_said_exactly_and_only_when_nothing_calls_for_it(
    tmp_path,
) -> None:
    quiet = CycleFinished(
        cycle_id="c1",
        finished_at=MOMENT,
        status=CycleStatus.COMPLETE,
        stages=(CycleStage(name="decisions", outcome=StageOutcome.RAN),),
        securities_asked=1,
        securities_priced=1,
        decisions=(DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),),
        unchanged=("KO",),
    )

    rendered = render(
        CycleRecord(
            started=CycleStarted(cycle_id="c1", started_at=MOMENT), finished=quiet
        ),
        CycleLog(),
    )

    assert NO_ACTION in rendered

    with_refusal = CycleFinished(
        cycle_id="c2",
        finished_at=MOMENT,
        status=CycleStatus.COMPLETE,
        stages=quiet.stages,
        securities_asked=2,
        securities_priced=1,
        refusals=("HYPE: no price came back",),
        decisions=quiet.decisions,
        unchanged=("KO",),
        attention=("HYPE: no price came back",),
    )

    rendered = render(
        CycleRecord(
            started=CycleStarted(cycle_id="c2", started_at=MOMENT),
            finished=with_refusal,
        ),
        CycleLog(),
    )

    assert NO_ACTION not in rendered
    assert "Consider today:" in rendered


# ── 15: unknown schemas refused, never pooled ───────────────────────


def test_unknown_cycle_schemas_are_counted_and_never_pooled(tmp_path) -> None:
    store = DailyCycleStore(tmp_path / "cycles")

    store.append_started(CycleStarted(cycle_id="c1", started_at=MOMENT))
    store.append_finished(
        CycleFinished(
            cycle_id="c1",
            finished_at=MOMENT,
            status=CycleStatus.COMPLETE,
            stages=(),
            decisions=(DecisionSummary(symbol="KO", state="PREPARE", rationale="r"),),
        )
    )

    with store.path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"schema": 9, "kind": "finished", "cycle_id": "c9"}))
        handle.write("\nnot json at all\n")

    log = store.log()

    assert len(log.records) == 1
    assert log.skipped_records == 2
    assert not log.is_complete_stream

    rendered = render(log.records[0], log)

    assert "could not be read" in rendered


# ── 12–14: what this slice must not introduce ───────────────────────


def test_the_cycle_module_reaches_no_forbidden_path() -> None:
    """AST over the new modules: no model, news, trade or message import."""

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
    """No resolved/corrected; a gap is never a claim about the company."""

    _, store, _ = cycle_run(tmp_path, decision("KO", "PREPARE"))

    rendered = capsys.readouterr().out.casefold()

    for banned in ("resolved", "corrected", "weak business", "poor quality"):
        assert banned not in rendered


def test_the_store_lives_under_the_evidence_root(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("MOVRVEST_EVIDENCE_ROOT", str(tmp_path))

    store = DailyCycleStore()

    assert str(store.path).startswith(str(tmp_path))
