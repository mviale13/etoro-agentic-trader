"""One explicit Daily CIO cycle, as a durable fact.

#217 measured the absence this module fills: no cycle identity existed
anywhere, so *"nothing changed"* and *"the cycle failed"* were
indistinguishable from every surface, and the decision journal was
written by page views — the one recommendation change the measurement
caught entered the journal because a page was opened.

**The lifecycle is two events and a derivation** (#217 §9). A single
final record would leave *never started* indistinguishable from
*started and interrupted* whenever the process died before the write.
So STARTED is appended before the first network action, one terminal
event is appended when orchestration finishes, and a STARTED with no
terminal event is *derived* as interrupted — *no terminal event is ever
manufactured for a hard process kill*; the dangling STARTED is itself
the record of the interruption.

**Execution status and evidence sufficiency are separate dimensions**
(#217 §9). COMPLETE means every required stage ran — never that every
provider answered, every security was evidenced, or every security
received a recommendation. Refusals and evidence gaps live *inside* a
COMPLETE cycle and stay visible. And information availability is never
a proxy for company quality: a gap constrains the claim and the
permissible action, not the company's standing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.capital_envelope import CapitalActionEnvelope


class CycleStatus(StrEnum):
    """How the cycle's orchestration ended. Terminal states only.

    The fourth presentation state — interrupted — is deliberately not a
    member: it is never written, only derived from a STARTED that no
    terminal event followed.
    """

    #: Every required stage ran. Item-level failures and refusals are
    #: allowed, counted, and shown — they are the other dimension.
    COMPLETE = "complete"

    #: A required stage failed or was skipped, and a useful decision
    #: result was still produced.
    PARTIAL = "partial"

    #: No useful decision pass could be completed.
    FAILED = "failed"


class StageOutcome(StrEnum):
    RAN = "ran"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CycleStage:
    """One required stage, and what happened to it — in words when it failed."""

    name: str
    outcome: StageOutcome

    #: The failure as it was worded at the time. Empty when the stage ran.
    because: str = ""


@dataclass(frozen=True, slots=True)
class DecisionSummary:
    """One security's disposition and course, as the cycle's pass produced them.

    Carries only facts available at cycle time: the state, the
    contemporaneous rationale the journal already holds, the evidence
    date the decision itself carries — and the **course**, which is
    `workspace.action` as the existing pipeline built it. The action is
    the canonical answer to *what should the investor consider*, and it
    is carried verbatim: kind, statement, reason, and whether the
    existing `ActionKind` says it asks for something. Nothing here
    re-infers actionability from a decision-state string, and never a
    later-rebuilt synthesis presented as contemporaneous.
    """

    symbol: str
    state: str
    rationale: str
    conviction: int | None = None
    evidence_as_of: str = ""

    #: The course, from the pipeline's own `ExecutiveAction` — carried,
    #: never reinterpreted.
    action_kind: str = ""
    action_statement: str = ""
    action_because: str = ""
    asks_for_something: bool = False

    #: The Capital Action Envelope for an OPEN, ADD or policy-compliance
    #: REDUCE course — display-only, normalized, and optional twice
    #: over: absent on non-capital courses, and absent on records
    #: written before the envelope existed, which decode exactly as
    #: they always did.
    envelope: CapitalActionEnvelope | None = None


class ComparisonOutcome(StrEnum):
    """What the cycle's change comparison rested on. Typed, never guessed.

    A nullable prior-id whose meaning has to be inferred is exactly the
    ambiguity the two-event lifecycle removed from status; the
    comparison gets the same treatment.
    """

    #: The first valid cycle: no previous completed cycle exists, so no
    #: change classification is claimed at all.
    INITIAL_BASELINE = "initial_baseline"

    #: Compared against one named prior cycle's terminal record.
    COMPARED = "compared"

    #: The comparison was refused — the held stream is incomplete, or no
    #: useful decision pass ran — and no movement was classified.
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class ComparisonBasis:
    """A typed basis whose shape is enforced, not described.

    Each outcome permits exactly one field pattern, checked at
    construction — so a stored record carrying a contradictory shape
    (a baseline with a prior id, a comparison with no prior, a refusal
    with no reason) cannot be constructed at all, which is what makes
    it *unreadable* on decode rather than quietly reinterpreted.
    Whitespace is not content: a blank-padded id or reason is empty.
    """

    outcome: ComparisonOutcome

    #: The prior cycle compared against. Filled exactly when COMPARED.
    prior_cycle_id: str = ""

    #: Why the comparison was refused. Filled exactly when REFUSED.
    because: str = ""

    def __post_init__(self) -> None:
        prior = bool(self.prior_cycle_id.strip())
        reason = bool(self.because.strip())

        valid = {
            ComparisonOutcome.INITIAL_BASELINE: not prior and not reason,
            ComparisonOutcome.COMPARED: prior and not reason,
            ComparisonOutcome.REFUSED: not prior and reason,
        }[self.outcome]

        if not valid:
            raise ValueError(
                f"a {self.outcome.value} basis does not carry "
                f"prior_cycle_id={self.prior_cycle_id!r}, because={self.because!r}"
            )


@dataclass(frozen=True, slots=True)
class CycleStarted:
    cycle_id: str
    started_at: datetime


@dataclass(frozen=True, slots=True)
class CycleFinished:
    cycle_id: str
    finished_at: datetime
    status: CycleStatus
    stages: tuple[CycleStage, ...]

    #: Acquisition facts: how many were asked and priced, and each
    #: refusal in the cycle's own words ("HYPE: no price came back").
    securities_asked: int = 0
    securities_priced: int = 0
    refusals: tuple[str, ...] = ()

    #: The decision pass over the active book.
    decisions: tuple[DecisionSummary, ...] = ()

    #: What the movement below rests on. INITIAL_BASELINE and REFUSED
    #: carry empty movement — an unclassified day, never a quiet one.
    comparison: ComparisonBasis = ComparisonBasis(
        outcome=ComparisonOutcome.REFUSED,
        because="the record carries no comparison basis",
    )

    #: Movement against the named previous cycle's terminal record —
    #: computed from cycle-tagged facts only, never from page-view
    #: journal entries, and only under a COMPARED basis: an incomplete
    #: stream refuses the comparison outright, because the unreadable
    #: record may be the actual previous cycle.
    newly_produced: tuple[str, ...] = ()
    changed: tuple[str, ...] = ()
    unchanged: tuple[str, ...] = ()

    #: What deserves the investor's eye: the changed dispositions, with
    #: refusals beside them — visible inside COMPLETE, per the ruling.
    attention: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CycleRecord:
    """One cycle as a reader sees it: the pairing of its events."""

    started: CycleStarted
    finished: CycleFinished | None = None

    @property
    def cycle_id(self) -> str:
        return self.started.cycle_id

    @property
    def is_interrupted(self) -> bool:
        """STARTED with no terminal event.

        Derived, never stored. Rendered as interrupted — never as
        COMPLETE, PARTIAL, FAILED, or "nothing changed".
        """

        return self.finished is None


@dataclass(frozen=True, slots=True)
class CycleLog:
    """Every cycle held, oldest first, with the stream's own honesty.

    Three defect counts travel separately, because they are three
    different facts: malformed or shape-invalid lines are *unreadable*,
    valid JSON under an unknown schema is *unsupported* (refused, never
    misread — #216's rule, applied to cycles), and decoded events that
    form no valid two-event lifecycle are *anomalies*. A log holding
    any of the three does not claim a complete lifecycle.
    """

    records: tuple[CycleRecord, ...] = ()

    #: Malformed JSON, or a current-schema record whose shape does not
    #: decode — including a comparison basis carrying a contradictory
    #: shape, which is refused at construction.
    unreadable_records: int = 0

    #: Valid JSON under a schema this reader does not know. Not
    #: unreadable — a future format is refused, never misread.
    unsupported_schemas: int = 0

    #: Events that decode but form no valid two-event lifecycle: a
    #: FINISHED with no STARTED, a second STARTED or FINISHED for one
    #: cycle_id, a terminal before its start. Counted and disclosed,
    #: never pooled into a valid record — and a byte-identical duplicate
    #: is still a second lifecycle event, with no recovery precedence
    #: invented for it.
    lifecycle_anomalies: int = 0

    @property
    def is_complete_stream(self) -> bool:
        """True only when all three defect counts are zero."""

        return (
            self.unreadable_records == 0
            and self.unsupported_schemas == 0
            and self.lifecycle_anomalies == 0
        )

    @property
    def dangling(self) -> tuple[CycleRecord, ...]:
        """Every started-and-never-ended cycle, for disclosure."""

        return tuple(record for record in self.records if record.is_interrupted)

    def latest_terminal(self) -> CycleFinished | None:
        """The newest cycle that ended with a decision-bearing terminal.

        The comparison base for produced/changed/unchanged: the previous
        cycle's own record, and nothing else — a page view cannot enter
        this derivation because a page view writes no cycle event.
        """

        for record in reversed(self.records):
            if record.finished is not None and record.finished.decisions:
                return record.finished

        return None


#: Said exactly, when nothing calls for action. It is a statement about
#: the cycle's findings, never an assessment that the portfolio is safe.
NO_ACTION = "No action suggested."


def movement(
    current: tuple[DecisionSummary, ...],
    previous: CycleFinished,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Produced / changed / unchanged, against one named previous cycle.

    Called only under a COMPARED basis. The no-previous case is not a
    parameter here any more: it is `INITIAL_BASELINE`, a typed state
    that classifies nothing — a first cycle has nothing to have changed
    *from*, and an incomplete stream refuses the comparison before this
    function is reached.
    """

    before = {entry.symbol: entry.state for entry in previous.decisions}

    produced = tuple(e.symbol for e in current if e.symbol not in before)
    changed = tuple(
        e.symbol for e in current if e.symbol in before and before[e.symbol] != e.state
    )
    unchanged = tuple(
        e.symbol for e in current if e.symbol in before and before[e.symbol] == e.state
    )

    return (produced, changed, unchanged)


def no_action_permitted(finished: CycleFinished) -> bool:
    """Whether `No action suggested.` may be said, and nothing weaker.

    All six, together: the cycle completed; a valid previous-cycle
    comparison exists; no disposition changed; no newly produced course
    asks for something; nothing was refused; and no required stage
    failed. PARTIAL, FAILED, initial-baseline and comparison-refused
    cycles never reach it — an unclassified or degraded day is not a
    quiet one. And when it is said, it is a statement about the cycle's
    findings, never an assessment that the portfolio is safe.
    """

    by_symbol = {entry.symbol: entry for entry in finished.decisions}

    asking_new = any(
        by_symbol[symbol].asks_for_something
        for symbol in finished.newly_produced
        if symbol in by_symbol
    )

    return (
        finished.status is CycleStatus.COMPLETE
        and finished.comparison.outcome is ComparisonOutcome.COMPARED
        and not finished.changed
        and not asking_new
        and not finished.refusals
        and all(stage.outcome is StageOutcome.RAN for stage in finished.stages)
    )
