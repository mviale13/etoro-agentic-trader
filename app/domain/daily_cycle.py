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

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

from app.domain.capital_envelope import CapitalActionEnvelope
from app.domain.decision_blocker import DecisionBlocker


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

    #: What the conviction is, in the deciding layer's own words: how it
    #: was computed, which state capped it, under which rule.
    #:
    #: Carried beside the number because a number alone reads as
    #: enthusiasm — AMD's 40 is `conviction-mean@1`'s REJECT cap, not a
    #: mean that happened to land on 40 — and a surface may print the
    #: figure only with this beside it. Empty on a record written before
    #: the decision carried one.
    conviction_basis: str = ""

    #: How many score families that conviction was computed over, and
    #: how many were expected. `None` on a record written before the
    #: counts existed — and **an unknown coverage is never read as a
    #: matching one**: a projection that cannot tell whether two
    #: convictions share a denominator withholds the ranking rather than
    #: assuming they do (the owner's ruling of 2026-08-21,
    #: prerequisite 2).
    conviction_participating: int | None = None
    conviction_expected: int | None = None

    #: The families that produced no score here, named. Missing
    #: evidence, and never a low score for them.
    conviction_absent_families: tuple[str, ...] = ()

    evidence_as_of: str = ""

    #: What stands between this case and its next state, named by the
    #: gate that stopped it rather than inferred from the state.
    #:
    #: None on a record written before blockers existed, which decodes
    #: exactly as it always did. A case that cleared every gate carries
    #: a blocker of kind `none` — a sentence, never an empty cell.
    blocker: DecisionBlocker | None = None

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


@dataclass(frozen=True, slots=True)
class RecordedHolding:
    """One **security** as the cycle saw it, with its share of the account.

    A security, not a trade. eToro reports a position per *trade*, so an
    account holding one security bought twice arrives from the broker as
    two rows — and `weight_pct` is the security's share of the account,
    computed once over the summed value. Recording the broker's rows
    unfolded therefore printed the whole share twice beside two partial
    values — a Weight column that counts a security once per trade and
    stops adding up to the account. Fold with `holdings_by_security`
    before constructing a `RecordedPortfolio`; the aggregate refuses a
    repeated symbol outright.

    The per-*position* view is a different fact with its own surface —
    `PortfolioSnapshot.holdings`, served by `/portfolio` and labelled
    "positions" there. This record is the per-security one, which is
    what makes it joinable with the cycle's own per-security decisions.
    """

    symbol: str
    market_value_usd: float

    #: None where the account reports no value to take a share of, or
    #: where the holding could not be resolved to a symbol. Never 0.0
    #: for either — #223's rule, carried into the record.
    weight_pct: float | None = None


def holdings_by_security(
    rows: Iterable[RecordedHolding],
) -> tuple[RecordedHolding, ...]:
    """One entry per security, largest first, from the broker's rows.

    The single implementation of "which securities does this account
    hold, and how much of each" for the cycle record — used when the
    record is *written* from the broker's positions and when a record
    written before the fold existed is *read*. Two implementations is
    how the name and the percentage came to describe different holdings
    in `PortfolioService._largest_position`, and this is the same
    question one layer out.

    **The share is carried, never recomputed.** It is already the
    security's share of the account, derived where the account total was
    in hand; deriving it again here would need a total this function is
    deliberately not given. So two rows of one security that state
    *different* shares are a contradiction rather than an aggregation —
    the fold raises, and a stored record carrying one is unreadable
    rather than quietly reinterpreted.

    Ranked here as well as folded here, because a fold changes the
    ranking: two small positions can outweigh a larger single one, and a
    record whose order no longer matched its values would be a table the
    page could only fix by sorting — which is analysis the page may not
    do.
    """

    folded: dict[str, RecordedHolding] = {}

    for row in rows:
        held = folded.get(row.symbol)

        if held is None:
            folded[row.symbol] = row
            continue

        if held.weight_pct != row.weight_pct:
            raise ValueError(
                f"two {row.symbol} rows state different shares of the "
                f"account ({held.weight_pct} and {row.weight_pct})"
            )

        folded[row.symbol] = replace(
            held,
            market_value_usd=held.market_value_usd + row.market_value_usd,
        )

    return tuple(
        sorted(
            (
                replace(row, market_value_usd=round(row.market_value_usd, 2))
                for row in folded.values()
            ),
            key=lambda row: row.market_value_usd,
            reverse=True,
        )
    )


@dataclass(frozen=True, slots=True)
class RecordedAllocation:
    """One asset class against the investor's own target and range.

    `current_pct` is a **measurement of the account** and survives
    whatever happens to the plan. Everything else is the plan, and is
    None or empty wherever the allocation policy could not be
    validated — a refused plan leaves the account measured and states
    no target, which is not the same as a target of zero.
    """

    asset: str
    current_pct: float | None

    #: None exactly where the allocation policy was refused. A target
    #: is a statement of the investor's plan, and this platform states
    #: none where it could not read one.
    target_pct: float | None
    difference_pct: float | None

    #: The operating range the target sits inside. Tactical latitude,
    #: not a limit: being outside the target but inside the range is a
    #: normal state (owner ruling, 2026-08-24). Both None only on a
    #: record written before the ranges existed.
    minimum_pct: float | None = None
    maximum_pct: float | None = None

    #: "below_range" | "within_range" | "above_range" | "unmeasured",
    #: and the CIO's worded guidance for it. Empty on a pre-ruling
    #: record, which then carries no standing rather than a guessed one.
    standing: str = ""
    stated: str = ""


@dataclass(frozen=True, slots=True)
class RecordedPortfolio:
    """The account as the cycle read it, recorded rather than re-fetched.

    The cycle already builds a Brain, so it already holds this. Throwing
    it away meant a page wanting the portfolio had to acquire it again —
    which is exactly the spend a page view may not make. Recording it
    here is what lets the homepage show an account without touching a
    provider.

    Cash absence survives into the record: `available_cash_usd` and
    `cash_pct` are None where the broker stated no figure, and a
    measured zero stays 0.0.
    """

    total_value: float
    available_cash_usd: float | None = None
    cash_pct: float | None = None

    #: One entry per security, largest first — never one per broker
    #: position. Enforced at construction rather than described, the way
    #: `ComparisonBasis` enforces its own shape: a caller holding the
    #: broker's rows folds them with `holdings_by_security` first, and
    #: one that does not cannot build this object at all.
    holdings: tuple[RecordedHolding, ...] = ()

    #: The receipt-time wording from #223 — when eToro's account
    #: response arrived, never when eToro observed the account.
    observed: str = ""

    #: The account against the investor's own strategy, compared at
    #: cycle time because that is where both halves are in hand. The
    #: measured share is the account's; the target, range and standing
    #: are the *validated* `StrategicAllocation`'s and appear only when
    #: there is one. A difference of None is unmeasured, never zero.
    allocations: tuple[RecordedAllocation, ...] = ()

    #: The CIO's account of the account's shape, composed once during
    #: the cycle from that cycle's own portfolio reading and the active
    #: policy. Rendered from this record — a page recomputes nothing,
    #: so no two surfaces can disagree about what the review said.
    #: Empty on a pre-ruling record and wherever no allocation could be
    #: read, which the refusal below then words.
    allocation_guidance: str = ""
    allocation_guidance_refused: str = ""

    #: Why the allocation *policy* itself could not be read — the
    #: `CapitalPolicyReading`'s own sentence, verbatim. A different
    #: fact from the refusal above: that one says no allocation could
    #: be measured, this one says the plan to measure it against is
    #: missing or contradictory. Non-empty exactly where no target,
    #: range, standing or compliance judgment may be shown.
    allocation_policy_refused: str = ""

    #: None where any required comparison was unmeasured, and always
    #: None under a refused allocation policy — a plan this platform
    #: could not validate produces no compliance judgment at all.
    compliant: bool | None = None

    def __post_init__(self) -> None:
        symbols = [holding.symbol for holding in self.holdings]

        if len(symbols) != len(set(symbols)):
            repeated = sorted({s for s in symbols if symbols.count(s) > 1})

            raise ValueError(
                "a recorded portfolio holds one entry per security; "
                f"{', '.join(repeated)} appears more than once"
            )


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

    #: The account as this cycle read it. None on a cycle that could not
    #: read one, and on every record written before the field existed.
    portfolio: RecordedPortfolio | None = None

    #: Watched-but-unheld securities this cycle actually **evaluated**,
    #: carried in the same shape as a holding's decision because they
    #: went through the same pipeline.
    #:
    #: Empty by default and by design: evidencing a candidate costs a
    #: fundamentals request and evaluating one costs a pipeline pass, so
    #: a cycle pays for them only when asked (`--candidates N`). An
    #: empty tuple therefore means *none were evaluated*, which is not
    #: the same as *none were worth holding* — and no surface may read
    #: it as the second.
    candidates: tuple[DecisionSummary, ...] = ()


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
