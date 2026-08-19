"""One explicit Daily CIO cycle: acquire, decide, record, render.

The cycle spine #217's ruling approved — an explicit command and
nothing else: no scheduler, no daemon, no notifications, no queue.
The two stages are the components that already exist, run once each;
this module adds identity, order and a durable record, never judgment.

**STARTED is on disk before the first network action.** A process
killed anywhere after that leaves a STARTED with no terminal event —
which the next render discloses as interrupted, and which nothing ever
relabels as COMPLETE, FAILED, or "nothing changed".

**The comparison base is the previous cycle's own record.** Page views
still journal decisions (#217; the surface cutover is named follow-on
work, not this slice) — but they write no cycle event, so they cannot
manufacture or mask a change here.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.application.brain.brain_builder_service import BrainBuilderService
from app.application.learning.decision_journal import DecisionJournal
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.portfolio_briefing_service import (
    PortfolioBriefingService,
)
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
from app.repositories.json_event_repository import JsonEventRepository
from app.services.market_acquisition_service import MarketAcquisitionService

__all__ = ["run"]


def new_cycle_id() -> str:
    """Opaque, unique per invocation. Never derived from the clock alone."""

    return uuid.uuid4().hex[:12]


async def run(
    store: DailyCycleStore | None = None,
    acquisition: MarketAcquisitionService | None = None,
    brains: BrainBuilderService | None = None,
    briefings: PortfolioBriefingService | None = None,
) -> int:
    store = store or DailyCycleStore()

    # Yesterday's honesty before today's work: a cycle that started and
    # never ended is disclosed, not silently superseded.
    held = store.log()

    cycle_id = new_cycle_id()
    started = CycleStarted(cycle_id=cycle_id, started_at=datetime.now(UTC))

    # Durable before the first acquisition or network action — the one
    # write a hard kill cannot take back, and the whole reason "started
    # and interrupted" is distinguishable from "never started".
    store.append_started(started)

    stages: list[CycleStage] = []
    asked = priced = 0
    refusals: tuple[str, ...] = ()

    # ── stage 1: the explicit acquisition, once ─────────────────────
    try:
        acquired = await (acquisition or MarketAcquisitionService()).acquire()
    except Exception as error:
        stages.append(
            CycleStage(
                name="acquisition",
                outcome=StageOutcome.FAILED,
                because=f"{type(error).__name__}: {error}"[:300],
            )
        )
    else:
        asked = len(acquired.securities)
        priced = len(acquired.priced)
        refusals = tuple(
            f"{security.symbol}: no price came back"
            for security in acquired.securities
            if not security.priced
        )
        stages.append(CycleStage(name="acquisition", outcome=StageOutcome.RAN))

    # ── stage 2: the canonical decision pass over the active book ───
    decisions: tuple[DecisionSummary, ...] = ()

    try:
        brain = await (brains or BrainBuilderService()).build()

        service = briefings or PortfolioBriefingService(
            pipeline=ExecutivePipeline(
                journal=DecisionJournal(JsonEventRepository(), cycle_id=cycle_id)
            )
        )

        briefing = service.build(brain)
        workspaces = briefing.workspaces if briefing is not None else ()

        decisions = tuple(
            DecisionSummary(
                symbol=workspace.decision.symbol,
                state=workspace.decision.state.value,
                rationale=workspace.decision.rationale,
                conviction=workspace.decision.conviction,
                evidence_as_of=(
                    workspace.decision.evidence_as_of.stated()
                    if workspace.decision.evidence_as_of is not None
                    else ""
                ),
            )
            for workspace in workspaces
            if workspace.decision is not None
        )
        stages.append(CycleStage(name="decisions", outcome=StageOutcome.RAN))
    except Exception as error:
        stages.append(
            CycleStage(
                name="decisions",
                outcome=StageOutcome.FAILED,
                because=f"{type(error).__name__}: {error}"[:300],
            )
        )

    # ── status: which stages ran, and nothing about item coverage ───
    ran = {stage.name for stage in stages if stage.outcome is StageOutcome.RAN}

    if "decisions" not in ran or not decisions:
        # No useful decision pass. An acquisition alone fills stores
        # and answers none of the investor's five questions.
        status = CycleStatus.FAILED
    elif "acquisition" in ran:
        status = CycleStatus.COMPLETE
    else:
        status = CycleStatus.PARTIAL

    produced, changed, unchanged = movement(decisions, held.latest_terminal())

    by_symbol = {entry.symbol: entry for entry in decisions}
    attention = (
        tuple(
            f"{symbol}: now {by_symbol[symbol].state} — {by_symbol[symbol].rationale}"
            for symbol in changed
        )
        + refusals
    )

    finished = CycleFinished(
        cycle_id=cycle_id,
        finished_at=datetime.now(UTC),
        status=status,
        stages=tuple(stages),
        securities_asked=asked,
        securities_priced=priced,
        refusals=refusals,
        decisions=decisions,
        newly_produced=produced,
        changed=changed,
        unchanged=unchanged,
        attention=attention,
    )

    store.append_finished(finished)

    print(render(CycleRecord(started=started, finished=finished), held))

    return 0 if status is not CycleStatus.FAILED else 1


def render(record: CycleRecord, held_before: CycleLog) -> str:
    """The cycle as the investor reads it. Pure, for the tests.

    Distinguishes, in words that cannot be mistaken for each other:
    completed-and-changed, completed-and-nothing-changed,
    completed-with-gaps, partial, failed — and, from the prior log,
    started-but-never-ended. A failed cycle never says nothing changed;
    a completed one never says the evidence was complete; an absence is
    never a statement about a company; and nothing here calls a past
    dispute resolved.
    """

    lines = ["", f"DAILY CIO CYCLE — {record.cycle_id}", "=" * 60]

    # Disclosure of the stream's own limits and of interrupted runs.
    if not held_before.is_complete_stream:
        lines.append(
            f"{held_before.skipped_records} stored cycle record(s) could not "
            "be read; the lifecycle shown is derived from the readable ones "
            "only."
        )

    for dangling in held_before.dangling:
        lines.append(
            f"A previous cycle ({dangling.cycle_id}) started at "
            f"{dangling.started.started_at:%Y-%m-%d %H:%M UTC} and recorded "
            "no end — it was interrupted. Nothing is known about what it "
            "would have found."
        )

    finished = record.finished

    if finished is None:
        lines.append(
            "This cycle started and has recorded no end — it is interrupted, "
            "and no view of the day is claimed from it."
        )

        return "\n".join(lines)

    lines.append(f"Status: {finished.status.value.upper()}")

    for stage in finished.stages:
        worded = stage.outcome.value + (f" — {stage.because}" if stage.because else "")
        lines.append(f"  {stage.name}: {worded}")

    if finished.status is CycleStatus.FAILED:
        lines.append("")
        lines.append(
            "No useful decision pass was completed, so nothing can be said "
            "about what changed today. This is a failed cycle, not a quiet "
            "one."
        )

        return "\n".join(lines)

    lines.append("")
    lines.append(
        f"Acquisition: {finished.securities_priced} priced of "
        f"{finished.securities_asked} asked."
    )

    if finished.refusals:
        lines.append(
            f"Evidence gaps ({len(finished.refusals)}) — each constrains what "
            "can be said about that security, and says nothing about the "
            "business itself:"
        )
        lines.extend(f"  {refusal}" for refusal in finished.refusals)

    lines.append("")
    lines.append(
        f"Decisions: {len(finished.decisions)} securities considered — "
        f"{len(finished.newly_produced)} newly produced, "
        f"{len(finished.changed)} changed, {len(finished.unchanged)} unchanged."
    )

    if finished.changed:
        lines.append("Changed, with the rationale recorded at decision time:")
        by_symbol = {entry.symbol: entry for entry in finished.decisions}

        for symbol in finished.changed:
            entry = by_symbol[symbol]
            lines.append(f"  {symbol}: now {entry.state} — {entry.rationale}")
    elif finished.decisions:
        lines.append("No recommendation changed against the previous cycle.")

    lines.append("")

    if finished.changed or finished.refusals:
        lines.append("Consider today:")
        lines.extend(f"  {item}" for item in finished.attention)
    else:
        lines.append(NO_ACTION)

    return "\n".join(lines)
