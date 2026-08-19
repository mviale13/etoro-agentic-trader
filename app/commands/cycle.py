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
    ComparisonBasis,
    ComparisonOutcome,
    CycleFinished,
    CycleLog,
    CycleRecord,
    CycleStage,
    CycleStarted,
    CycleStatus,
    DecisionSummary,
    StageOutcome,
    movement,
    no_action_permitted,
)
from app.infrastructure.evidence.daily_cycle_store import DailyCycleStore
from app.repositories.json_event_repository import JsonEventRepository
from app.services.market_acquisition_service import MarketAcquisitionService

__all__ = ["run"]


def _failed_stage(name: str, error: Exception) -> CycleStage:
    """A stage failure, worded for the record rather than copied from it.

    Provider exceptions carry URLs, query parameters and sometimes
    credentials. What the durable record needs is which stage failed
    and what kind of failure it was — so the wording is built here from
    the stage's name and the exception's *class*, and the exception's
    own text never reaches the store or the render.
    """

    return CycleStage(
        name=name,
        outcome=StageOutcome.FAILED,
        because=f"the {name} stage failed ({type(error).__name__})",
    )


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
        stages.append(_failed_stage("acquisition", error))
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

        # The course comes from `workspace.action` and nowhere else —
        # the pipeline's own ExecutiveAction, carried verbatim. And no
        # security disappears: a workspace whose pass produced no
        # disposition or no course is *refused in words*, named for
        # which half was missing, rather than filtered out of the
        # cycle's account. Nothing manufactures an action and nothing
        # infers one from a decision state.
        carried: list[DecisionSummary] = []

        for workspace in workspaces:
            if workspace.decision is not None and workspace.action is not None:
                carried.append(
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
                        action_kind=workspace.action.kind.value,
                        action_statement=workspace.action.statement,
                        action_because=workspace.action.because,
                        asks_for_something=workspace.action.kind.asks_for_something,
                    )
                )
            elif workspace.decision is None:
                refusals = refusals + (
                    f"{workspace.symbol}: the decision pass produced no "
                    "disposition; this constrains what the cycle can say "
                    "and says nothing about the business",
                )
            else:
                refusals = refusals + (
                    f"{workspace.symbol}: the decision pass produced a "
                    "disposition and no course; this constrains what the "
                    "cycle can say and says nothing about the business",
                )

        decisions = tuple(carried)
        stages.append(CycleStage(name="decisions", outcome=StageOutcome.RAN))
    except Exception as error:
        stages.append(_failed_stage("decisions", error))

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

    # The comparison basis, typed and persisted — never a nullable id
    # whose meaning has to be guessed. An incomplete stream refuses the
    # comparison outright: the unreadable or anomalous record may be
    # the actual previous cycle, and a disclosure beside a derived
    # change would not make the change safe.
    previous = held.latest_terminal() if held.is_complete_stream else None

    if status is CycleStatus.FAILED:
        comparison = ComparisonBasis(
            outcome=ComparisonOutcome.REFUSED,
            because="no useful decision pass was completed",
        )
    elif not held.is_complete_stream:
        comparison = ComparisonBasis(
            outcome=ComparisonOutcome.REFUSED,
            because=(
                "the held cycle stream is incomplete "
                f"({held.unreadable_records} unreadable record(s), "
                f"{held.unsupported_schemas} unsupported-schema record(s), "
                f"{held.lifecycle_anomalies} lifecycle anomaly(ies)), and an "
                "unreadable record may be the actual previous cycle"
            ),
        )
    elif previous is None:
        comparison = ComparisonBasis(outcome=ComparisonOutcome.INITIAL_BASELINE)
    else:
        comparison = ComparisonBasis(
            outcome=ComparisonOutcome.COMPARED,
            prior_cycle_id=previous.cycle_id,
        )

    if comparison.outcome is ComparisonOutcome.COMPARED and previous is not None:
        produced, changed, unchanged = movement(decisions, previous)
    else:
        produced, changed, unchanged = (), (), ()

    by_symbol = {entry.symbol: entry for entry in decisions}

    # Attention: changed dispositions, newly produced courses that ask
    # for something, refusals, and failed required stages — in that
    # order. A newly produced course that asks for nothing is still
    # newly considered, and is reported as that rather than as an
    # action.
    attention = (
        tuple(
            f"{symbol}: now {by_symbol[symbol].state} — {by_symbol[symbol].rationale}"
            for symbol in changed
        )
        + tuple(
            f"{symbol}: {by_symbol[symbol].action_statement} "
            f"({by_symbol[symbol].action_kind})"
            for symbol in produced
            if by_symbol[symbol].asks_for_something
        )
        + refusals
        + tuple(
            f"the {stage.name} stage failed — {stage.because}"
            for stage in stages
            if stage.outcome is StageOutcome.FAILED
        )
    )

    finished = CycleFinished(
        cycle_id=cycle_id,
        finished_at=datetime.now(UTC),
        status=status,
        stages=tuple(stages),
        securities_asked=asked,
        securities_priced=priced,
        refusals=refusals,
        comparison=comparison,
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
            "The held cycle stream is incomplete — "
            f"{held_before.unreadable_records} unreadable record(s), "
            f"{held_before.unsupported_schemas} unsupported-schema record(s), "
            f"{held_before.lifecycle_anomalies} lifecycle anomaly(ies); the "
            "lifecycle shown is derived from the readable ones only."
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

    comparison = finished.comparison

    if comparison.outcome is ComparisonOutcome.INITIAL_BASELINE:
        lines.append(
            "Initial cycle recorded; no previous completed cycle exists for "
            "change comparison."
        )
        lines.append(
            f"Current courses ({len(finished.decisions)} securities considered):"
        )
        lines.extend(
            f"  {entry.symbol}: {entry.state} — {entry.action_statement} "
            f"({entry.action_kind})"
            for entry in finished.decisions
        )
    elif comparison.outcome is ComparisonOutcome.REFUSED:
        lines.append(
            f"Change comparison refused: {comparison.because}. No changed, "
            "unchanged or newly-produced classification is claimed for this "
            "cycle."
        )
        lines.append(
            f"Current courses ({len(finished.decisions)} securities considered):"
        )
        lines.extend(
            f"  {entry.symbol}: {entry.state} — {entry.action_statement} "
            f"({entry.action_kind})"
            for entry in finished.decisions
        )
    else:
        lines.append(
            f"Decisions (against cycle {comparison.prior_cycle_id}): "
            f"{len(finished.decisions)} securities considered — "
            f"{len(finished.newly_produced)} newly produced, "
            f"{len(finished.changed)} changed, "
            f"{len(finished.unchanged)} unchanged."
        )

        by_symbol = {entry.symbol: entry for entry in finished.decisions}

        if finished.changed:
            lines.append("Changed, with the rationale recorded at decision time:")

            for symbol in finished.changed:
                entry = by_symbol[symbol]
                lines.append(f"  {symbol}: now {entry.state} — {entry.rationale}")

        if finished.newly_produced:
            lines.append("Newly considered:")

            for symbol in finished.newly_produced:
                entry = by_symbol[symbol]
                course = (
                    f" — {entry.action_statement} ({entry.action_kind})"
                    if entry.asks_for_something
                    else f" ({entry.state}; its course asks for nothing yet)"
                )
                lines.append(f"  {symbol}{course}")

        if not finished.changed and not finished.newly_produced:
            lines.append("No recommendation changed against the previous cycle.")

    lines.append("")

    if no_action_permitted(finished):
        lines.append(NO_ACTION)
    elif finished.attention:
        lines.append("Consider today:")
        lines.extend(f"  {item}" for item in finished.attention)

    return "\n".join(lines)
