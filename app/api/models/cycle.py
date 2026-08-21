"""The latest recorded CIO cycle, as an investor surface reads it.

**A projection, not a second decision layer.** Everything here is
carried from what `movrvest cycle` already recorded: the lifecycle, the
comparison basis, and each security's course exactly as the pipeline
produced it. Nothing is recomputed, re-inferred or re-worded, and no
field exists that a page could use to reach a conclusion the cycle did
not reach.

Three distinctions the domain draws are preserved here rather than
flattened, because flattening any of them is how a page starts lying:

- **Interrupted is not a status.** `CycleStatus` deliberately has no
  such member — it is derived from a STARTED that no terminal followed —
  so the presentation state carries it as its own case and never as
  COMPLETE, FAILED or "nothing changed".
- **A newer failure is not skipped in favour of an older success.** The
  latest attempt is always what `execution` describes. An older
  completed cycle may travel beside it only as `last_known`, carrying
  its own date so it can never be read as current.
- **`No action suggested.` is not a default.** It appears only where the
  domain's own six-condition predicate permits it, and it is a statement
  about the cycle's findings rather than an assessment that the
  portfolio is safe.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app.domain.capital_envelope import CapitalActionEnvelope
from app.domain.daily_cycle import (
    NO_ACTION,
    CycleFinished,
    CycleLog,
    CycleRecord,
    DecisionSummary,
    RecordedPortfolio,
    no_action_permitted,
)
from app.domain.decision_blocker import DecisionBlocker


class CycleExecution(StrEnum):
    """What happened to the latest recorded attempt.

    `CycleStatus`'s three terminal members, plus the two states that are
    not statuses at all: nothing recorded, and a start with no terminal.
    """

    NONE_RECORDED = "none_recorded"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    PARTIAL = "partial"
    COMPLETE = "complete"


class StageResponse(BaseModel):
    name: str
    outcome: str

    #: The failure in the words used at the time. Empty when it ran.
    because: str = ""


class EnvelopeResponse(BaseModel):
    """The Capital Action Envelope, carried with its own sentence.

    `stated` is the domain's wording. The numeric fields travel beside
    it so a surface can lay them out, never so it can compose a
    different sentence from them.
    """

    kind: str
    stated: str
    policy_source: str
    policy_version: str
    evidence_ceiling: str
    capacity_ceiling_pct: float | None
    final_pct: float | None
    binding_constraint: str
    because: str
    named_gaps: list[str]
    quality_authority: str | None
    starter_capped: bool
    price_as_of: str
    portfolio_as_of: str
    liquidity: str

    @classmethod
    def of(cls, envelope: CapitalActionEnvelope) -> EnvelopeResponse:
        return cls(
            kind=envelope.kind.value,
            stated=envelope.stated,
            policy_source=envelope.policy_source,
            policy_version=envelope.policy_version,
            evidence_ceiling=envelope.evidence_ceiling,
            capacity_ceiling_pct=envelope.capacity_ceiling_pct,
            final_pct=envelope.final_pct,
            binding_constraint=envelope.binding_constraint,
            because=envelope.because,
            named_gaps=list(envelope.named_gaps),
            quality_authority=(
                None
                if envelope.quality_authority is None
                else envelope.quality_authority.value
            ),
            starter_capped=envelope.starter_capped,
            price_as_of=envelope.price_as_of,
            portfolio_as_of=envelope.portfolio_as_of,
            liquidity=envelope.liquidity,
        )


class BlockerResponse(BaseModel):
    """What stands in the way, as the gate that stopped it named it.

    Every field is carried. The page renders `stated` and never
    composes a sentence from `kind`: the kind is for grouping, and an
    investor-facing cause is worded where the decision is made.
    """

    kind: str
    stated: str

    #: The analysts' favourable verdicts that survive this blocker,
    #: quoted. Empty where the gate is itself about the business.
    despite: list[str]

    #: What this ruling does not claim. Empty where the claim would be
    #: false — a quality gate *is* a statement about the business.
    does_not_say: str

    @classmethod
    def of(cls, blocker: DecisionBlocker) -> BlockerResponse:
        return cls(
            kind=blocker.kind.value,
            stated=blocker.stated,
            despite=list(blocker.despite),
            does_not_say=blocker.does_not_say,
        )


class CourseResponse(BaseModel):
    """One security's disposition and course, carried verbatim."""

    symbol: str
    disposition: str
    rationale: str
    conviction: int | None

    #: What the conviction is. Empty on a record written before the
    #: decision carried one — and a surface shows the number only where
    #: this is present, because a bare figure reads as enthusiasm.
    conviction_basis: str

    evidence_as_of: str

    action_kind: str
    action_statement: str
    action_because: str
    asks_for_something: bool

    envelope: EnvelopeResponse | None

    #: Null on a record written before blockers existed. Never
    #: substituted: an unknown cause is not "nothing blocks progress".
    blocker: BlockerResponse | None

    @classmethod
    def of(cls, entry: DecisionSummary) -> CourseResponse:
        return cls(
            symbol=entry.symbol,
            disposition=entry.state,
            rationale=entry.rationale,
            conviction=entry.conviction,
            conviction_basis=entry.conviction_basis,
            evidence_as_of=entry.evidence_as_of,
            action_kind=entry.action_kind,
            action_statement=entry.action_statement,
            action_because=entry.action_because,
            asks_for_something=entry.asks_for_something,
            envelope=(
                None if entry.envelope is None else EnvelopeResponse.of(entry.envelope)
            ),
            blocker=(
                None if entry.blocker is None else BlockerResponse.of(entry.blocker)
            ),
        )


class HoldingResponse(BaseModel):
    symbol: str
    market_value_usd: float

    #: Null where the share could not be computed — never 0.0 for it.
    weight_pct: float | None


class AllocationResponse(BaseModel):
    """One asset class against the investor's own target."""

    asset: str
    current_pct: float | None
    target_pct: float

    #: Null where the comparison could not be made. An unmeasured
    #: difference is not a difference of zero, and is never credited as
    #: sitting on target.
    difference_pct: float | None


class RecordedPortfolioResponse(BaseModel):
    """The account as the cycle recorded it — not as a page re-fetched it."""

    total_value: float
    available_cash_usd: float | None
    cash_pct: float | None
    observed: str
    holdings: list[HoldingResponse]
    allocations: list[AllocationResponse]

    #: Null where any required comparison was unmeasured.
    compliant: bool | None

    @classmethod
    def of(cls, portfolio: RecordedPortfolio) -> RecordedPortfolioResponse:
        return cls(
            total_value=portfolio.total_value,
            available_cash_usd=portfolio.available_cash_usd,
            cash_pct=portfolio.cash_pct,
            observed=portfolio.observed,
            holdings=[
                HoldingResponse(
                    symbol=holding.symbol,
                    market_value_usd=holding.market_value_usd,
                    weight_pct=holding.weight_pct,
                )
                for holding in portfolio.holdings
            ],
            allocations=[
                AllocationResponse(
                    asset=item.asset,
                    current_pct=item.current_pct,
                    target_pct=item.target_pct,
                    difference_pct=item.difference_pct,
                )
                for item in portfolio.allocations
            ],
            compliant=portfolio.compliant,
        )


class LastKnownResponse(BaseModel):
    """An older completed cycle, and the date that keeps it from reading as now."""

    cycle_id: str
    finished_at: datetime
    status: str
    courses: list[CourseResponse]


class CycleReviewResponse(BaseModel):
    """The latest recorded cycle, and nothing a page could compute itself."""

    execution: CycleExecution

    cycle_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    stages: list[StageResponse] = []

    #: `initial_baseline`, `compared` or `refused`. None where the latest
    #: attempt produced no terminal record to carry one.
    comparison_outcome: str | None = None
    comparison_prior_cycle_id: str = ""
    comparison_because: str = ""

    securities_asked: int = 0
    securities_priced: int = 0
    refusals: list[str] = []

    newly_produced: list[str] = []
    changed: list[str] = []
    unchanged: list[str] = []
    attention: list[str] = []

    courses: list[CourseResponse] = []

    #: Exactly `NO_ACTION`, or null. Never a softer phrase, and never a
    #: default: the domain predicate is the only way this is filled.
    no_action_suggested: str | None = None

    #: The stream's own honesty, carried rather than summarised away. An
    #: incomplete stream permits no movement claim, which is why the
    #: counts travel with the record.
    stream_complete: bool = True
    unreadable_records: int = 0
    unsupported_schemas: int = 0
    lifecycle_anomalies: int = 0

    #: Present only when the latest attempt did not itself produce
    #: courses and an older completed cycle exists.
    last_known: LastKnownResponse | None = None

    #: The account as this cycle recorded it. Null where the cycle could
    #: not read one, and on every record written before it was carried —
    #: a page shows nothing rather than fetching its own.
    portfolio: RecordedPortfolioResponse | None = None

    #: Watched-but-unheld securities this cycle **evaluated**, ordered by
    #: the conviction the Artificial CIO assigned, highest first — where
    #: those convictions are comparable at all.
    #:
    #: Empty means none were evaluated — which a surface must not render
    #: as "nothing is worth considering". Evaluating candidates costs
    #: provider and pipeline calls, so a cycle does it only when asked.
    candidates: list[CourseResponse] = []

    #: Whether the order above is a ranking. False where the recorded
    #: convictions were computed over different score families, or where
    #: the record does not say which — the list is then by symbol, and a
    #: surface may not present it as an order of merit.
    candidates_ranked: bool = False

    @classmethod
    def from_log(cls, log: CycleLog) -> CycleReviewResponse:
        """Project the stored log. Pure, and free of any I/O."""

        if not log.records:
            return cls(
                execution=CycleExecution.NONE_RECORDED,
                stream_complete=log.is_complete_stream,
                unreadable_records=log.unreadable_records,
                unsupported_schemas=log.unsupported_schemas,
                lifecycle_anomalies=log.lifecycle_anomalies,
            )

        latest: CycleRecord = log.records[-1]

        if latest.finished is None:
            # Interrupted. The older completed cycle is offered beside
            # it, dated — never in place of it.
            return cls(
                execution=CycleExecution.INTERRUPTED,
                cycle_id=latest.cycle_id,
                started_at=latest.started.started_at,
                last_known=_last_known(log, exclude=latest.cycle_id),
                stream_complete=log.is_complete_stream,
                unreadable_records=log.unreadable_records,
                unsupported_schemas=log.unsupported_schemas,
                lifecycle_anomalies=log.lifecycle_anomalies,
            )

        finished = latest.finished

        return cls(
            execution=CycleExecution(finished.status.value),
            cycle_id=latest.cycle_id,
            started_at=latest.started.started_at,
            finished_at=finished.finished_at,
            stages=[
                StageResponse(
                    name=stage.name,
                    outcome=stage.outcome.value,
                    because=stage.because,
                )
                for stage in finished.stages
            ],
            comparison_outcome=finished.comparison.outcome.value,
            comparison_prior_cycle_id=finished.comparison.prior_cycle_id,
            comparison_because=finished.comparison.because,
            securities_asked=finished.securities_asked,
            securities_priced=finished.securities_priced,
            refusals=list(finished.refusals),
            newly_produced=list(finished.newly_produced),
            changed=list(finished.changed),
            unchanged=list(finished.unchanged),
            attention=list(finished.attention),
            courses=[CourseResponse.of(entry) for entry in finished.decisions],
            no_action_suggested=(NO_ACTION if no_action_permitted(finished) else None),
            last_known=(
                None
                if finished.decisions
                else _last_known(log, exclude=latest.cycle_id)
            ),
            portfolio=(
                None
                if finished.portfolio is None
                else RecordedPortfolioResponse.of(finished.portfolio)
            ),
            # Ordered here, from the conviction the pipeline already
            # assigned. Ordering is priority, never certainty — and a
            # candidate with no conviction is never placed above one
            # that has it.
            #
            # **Only where the convictions share a denominator.** Two
            # numbers averaged over different score families are not two
            # points on one scale, and an order asserts that they are
            # (the owner's ruling of 2026-08-21, prerequisite 2). Where
            # they do not, the candidates come back by symbol — an
            # order that is obviously not a judgment — and a surface
            # reads `candidates_ranked` before calling it a ranking.
            candidates=[
                CourseResponse.of(entry) for entry in _ordered(finished.candidates)
            ],
            candidates_ranked=_comparable_coverage(finished.candidates),
            stream_complete=log.is_complete_stream,
            unreadable_records=log.unreadable_records,
            unsupported_schemas=log.unsupported_schemas,
            lifecycle_anomalies=log.lifecycle_anomalies,
        )


def _comparable_coverage(entries: Sequence[DecisionSummary]) -> bool:
    """Whether these convictions were computed over the same families.

    **Counts are not enough**, and neither is silence. Two securities
    judged on four of five families are not comparable when one is
    missing business quality and the other valuation, so the comparison
    is over the absent-family tuples. And a record that does not say —
    written before the counts existed — is not evidence that they
    matched: an entry carrying a conviction and no coverage makes the
    whole group incomparable rather than assumed-uniform.
    """

    judged = [entry for entry in entries if entry.conviction is not None]

    if any(entry.conviction_participating is None for entry in judged):
        return False

    return len({entry.conviction_absent_families for entry in judged}) <= 1


def _ordered(entries: Sequence[DecisionSummary]) -> list[DecisionSummary]:
    """Highest conviction first where that means something; by symbol otherwise."""

    if not _comparable_coverage(entries):
        return sorted(entries, key=lambda item: item.symbol)

    return sorted(
        entries,
        key=lambda item: (item.conviction is not None, item.conviction or 0),
        reverse=True,
    )


def _last_known(log: CycleLog, *, exclude: str) -> LastKnownResponse | None:
    """The newest earlier cycle that actually produced courses.

    Offered only beside a latest attempt that produced none, and always
    with its own `finished_at`, so a stale success can never be read as
    the current state of the account.
    """

    for record in reversed(log.records):
        if record.cycle_id == exclude or record.finished is None:
            continue

        finished: CycleFinished = record.finished

        if not finished.decisions:
            continue

        return LastKnownResponse(
            cycle_id=record.cycle_id,
            finished_at=finished.finished_at,
            status=finished.status.value,
            courses=[CourseResponse.of(entry) for entry in finished.decisions],
        )

    return None
