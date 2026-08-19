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
    """One security's disposition, as the cycle's pass produced it.

    Carries only facts available at cycle time: the state, the
    contemporaneous rationale the journal already holds, and the
    evidence date the decision itself carries. Never a later-rebuilt
    synthesis presented as contemporaneous.
    """

    symbol: str
    state: str
    rationale: str
    conviction: int | None = None
    evidence_as_of: str = ""


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

    #: Movement against the previous cycle's terminal record — computed
    #: from cycle-tagged facts only, never from page-view journal
    #: entries, so page traffic can never manufacture a change here.
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

    `skipped_records` counts non-empty stored lines this reader could
    not decode — unknown future schemas and unreadable lines, refused
    and counted rather than pooled (#216's rule, applied to cycles).
    A log with skipped lines does not claim a complete lifecycle.
    """

    records: tuple[CycleRecord, ...] = ()
    skipped_records: int = 0

    @property
    def is_complete_stream(self) -> bool:
        return self.skipped_records == 0

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
    previous: CycleFinished | None,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    """Produced / changed / unchanged, against the previous cycle only.

    With no previous terminal record every disposition is newly
    produced and no change is claimed — a first cycle has nothing to
    have changed *from*, and inventing a baseline would manufacture
    exactly the false movement this comparison exists to prevent.
    """

    if previous is None:
        return (tuple(entry.symbol for entry in current), (), ())

    before = {entry.symbol: entry.state for entry in previous.decisions}

    produced = tuple(e.symbol for e in current if e.symbol not in before)
    changed = tuple(
        e.symbol for e in current if e.symbol in before and before[e.symbol] != e.state
    )
    unchanged = tuple(
        e.symbol for e in current if e.symbol in before and before[e.symbol] == e.state
    )

    return (produced, changed, unchanged)
