"""The first layer permitted to interpret evidence, and the fence around it.

Everything before this establishes knowledge and is forbidden to read
meaning into it. Market context measures, the event layer records, the
journal remembers, the synthesist explains — and each was deliberately
built unable to judge. This layer judges, and because that permission is
new it is granted narrowly and structurally rather than by convention.

**A committee owns a question, not an asset.** The remit here is one
sentence and the output answers only it. There is no field capable of
carrying *should I buy*, *is this a good investment* or *what is the
overall conviction* — not because the prompt discourages them, but
because the schema has nowhere to put them. A verdict is a member of a
two-value enumeration scoped to the remit, and adding a third meaning
would mean editing this file with the reason written down.

**Eligibility is structural.** A committee sees `MEASURED` and
`REPORTED` claims, and deterministic projections over them. It never
sees `ATTRIBUTED` or `INFERRED` claims, and it never sees synthesis
prose — *the synthesis is communication, not evidence*, and letting it
back in through the judgment door would launder a model's reading into
a model's premise.

**Confidence is established by code and the verdict by judgment.** Not
a style choice: §7 requires that confidence cannot secretly decide the
verdict, and the cleanest way to guarantee that is to have different
things produce them. Confidence counts independent supporting
observations; nothing in that count can flip `REACHES` to
`DOES_NOT_REACH`, and no verdict changes because a second reading
arrived.

**Not knowing is a successful outcome.** Three states, never collapsed:
a judgment was reached, the committee abstained because the eligible
evidence cannot answer its question, or no judgment exists because
execution failed. The middle one is the committee working.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.committee_protocol import CommitteeContract, StructuralVerdict
from app.domain.crypto_intelligence import ClaimType

#: The claim types a committee may reason over.
#:
#: Two, and the exclusions matter more than the inclusions.
#: `ATTRIBUTED` is somebody's opinion and would let a provider's
#: sentence become this platform's premise; `INFERRED` is this
#: platform's own reading, and feeding a reading into a judgment as
#: though it were a fact is how a system starts agreeing with itself.
ELIGIBLE_CLAIM_TYPES = frozenset({ClaimType.MEASURED, ClaimType.REPORTED})


def is_eligible(claim_type: ClaimType) -> bool:
    """Whether a claim of this type may reach a committee at all."""

    return claim_type in ELIGIBLE_CLAIM_TYPES


class Applicability(StrEnum):
    """Whether this question is economically meaningful for this asset.

    **Three states, and the committee decides which** — in its own
    economic terms, from its own rule. The framework owns the
    vocabulary because every committee needs the same three
    distinctions; it owns none of the reasoning, because the reasoning
    is what a committee is for.

    Routing applicability through a shared taxonomy was tried and
    rejected in PR #112: `TokenArchetype` was built to decide which
    questions an Asset Quality layer asks, and delegating to it made
    BTC and TAO come out identical when their problems are opposite.
    """

    #: The token's economic role makes this question meaningful.
    APPLICABLE = "applicable"

    #: The question is the wrong instrument for this asset. **An asset
    #: here is not judged adversely; it is not judged.**
    NOT_ECONOMICALLY_APPLICABLE = "not_economically_applicable"

    #: This platform cannot establish which of the two above is true.
    #: **Distinct from the second on purpose**: not knowing whether a
    #: question applies is not the same as knowing it does not.
    UNESTABLISHED = "unestablished"

    @property
    def is_applicable(self) -> bool:
        return self is Applicability.APPLICABLE


@dataclass(frozen=True, slots=True)
class ApplicabilityBasis:
    """Whether the question applies, why, and what that was read from.

    One object rather than the three-tuple PR #113 grew, because the
    third element was added under pressure and a fourth would have gone
    the same way. All three travel together because they are one answer:
    the state a caller branches on, the committee's economic reasoning
    for a reader, and the role that reasoning was drawn from.

    `economic_role` is absent exactly when no role is established —
    filling it with a guess would say this platform knew something it
    did not, and it is the field that later lets a *changed*
    applicability be attributed to changed understanding rather than
    reported as unexplained.
    """

    applicability: Applicability
    because: str
    economic_role: str | None = None

    @property
    def is_applicable(self) -> bool:
        return self.applicability.is_applicable


class JudgmentState(StrEnum):
    """Whether there is a judgment, and if not, which kind of not.

    §6, and the three must never collapse. An abstention is the
    committee succeeding at knowing its own limits; an unavailable
    judgment is the machinery failing. Reporting them as one would make
    a broken provider look like intellectual honesty.
    """

    #: A verdict was reached and survived validation.
    JUDGED = "judged"

    #: The committee read its eligible evidence and cannot answer its
    #: own question from it. A successful outcome.
    ABSTAINED = "abstained"

    #: No judgment exists because the machinery failed — off,
    #: unconfigured, unreachable, or a draft that failed validation.
    UNAVAILABLE = "unavailable"

    @property
    def stated(self) -> str:
        return {
            JudgmentState.JUDGED: "judged",
            JudgmentState.ABSTAINED: "abstained",
            JudgmentState.UNAVAILABLE: "no judgment available",
        }[self]


class Confidence(StrEnum):
    """How much independent evidence stands behind the verdict.

    **Established by code, never chosen by the judge**, which is what
    makes §7's independence structural rather than promised. It counts
    observations; it cannot reach the verdict, and the verdict cannot
    reach it.

    Categorical rather than a 0–100 score, because nothing measured
    here supports a continuous scale. Three independent readings are
    not "73% confident" — they are three readings, and saying so is the
    whole of what this platform knows.
    """

    #: One eligible observation supports it.
    SINGLE_OBSERVATION = "single_observation"

    #: Two or more independent eligible observations support it — a
    #: second mapped entity, a second metric, a second source.
    MULTIPLE_OBSERVATIONS = "multiple_observations"

    #: Supported across more than one recorded capture, so the journal
    #: says it has held rather than merely been seen once.
    OBSERVED_OVER_TIME = "observed_over_time"

    @property
    def stated(self) -> str:
        return {
            Confidence.SINGLE_OBSERVATION: "one supporting observation",
            Confidence.MULTIPLE_OBSERVATIONS: (
                "several independent supporting observations"
            ),
            Confidence.OBSERVED_OVER_TIME: (
                "supported across more than one recorded capture"
            ),
        }[self]

    @property
    def rank(self) -> int:
        """The order `confidence_from` assigns these, made explicit.

        **Not a score and not a scale**: the gap between 1 and 2 is not
        the gap between 2 and 3, and no arithmetic may be done on these
        numbers. The only thing they are for is telling two states apart
        when a later judgment is compared with an earlier one, which
        needs an order and nothing more.
        """

        return {
            Confidence.SINGLE_OBSERVATION: 1,
            Confidence.MULTIPLE_OBSERVATIONS: 2,
            Confidence.OBSERVED_OVER_TIME: 3,
        }[self]


class AbstentionReason(StrEnum):
    """Why a committee could not answer. Three, and never collapsed.

    They correspond exactly to the three questions that must be asked in
    order — *is this meaningful*, *can we establish whether it is*, and
    *do we have the evidence* — because collapsing them produces the two
    specific errors this slice was warned about: Bitcoin looking adverse
    for lacking mechanics it was never supposed to have, and Bittensor
    looking identical to Bitcoin when its problem is entirely different.
    """

    #: The question is the wrong instrument for this asset's economics.
    #: **Not an adverse finding**, and a surface must not render it as
    #: one.
    NOT_ECONOMICALLY_APPLICABLE = "not_economically_applicable"

    #: This platform cannot establish whether the question applies —
    #: the asset's economic role is not established, or no economic
    #: system is mapped to it. Not the same as knowing it does not
    #: apply.
    APPLICABILITY_UNESTABLISHED = "applicability_unestablished"

    #: The question applies, and the eligible evidence cannot answer it.
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

    @property
    def stated(self) -> str:
        return {
            AbstentionReason.NOT_ECONOMICALLY_APPLICABLE: (
                "this question is not economically meaningful for this asset, "
                "so it is left unanswered rather than answered adversely"
            ),
            AbstentionReason.APPLICABILITY_UNESTABLISHED: (
                "this platform cannot establish whether the question applies "
                "to this asset at all"
            ),
            AbstentionReason.INSUFFICIENT_EVIDENCE: (
                "the question applies and the eligible evidence cannot answer it"
            ),
        }[self]


@dataclass(frozen=True, slots=True)
class EligibleFinding:
    """One established fact a committee is allowed to reason over.

    Everything a committee sees arrives as one of these, and nothing
    reaches it any other way. `ref` is the handle a verdict cites;
    `established_by` says which layer computed it, because §8 requires
    that every comparison, share or duration was settled in code before
    the committee saw it.
    """

    ref: str
    stated: str

    claim_type: ClaimType

    #: The layer that established it — a claim, an arithmetic step over
    #: two claims, or a deterministic temporal projection.
    established_by: str

    #: Journal entry ids, where this came from the record. Traceable
    #: back to the observations, as §3 requires of a projection.
    observations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not is_eligible(self.claim_type):
            raise ValueError(
                f"{self.claim_type.value} evidence cannot reach a committee: "
                "only measured and reported facts are eligible for judgment."
            )


@dataclass(frozen=True, slots=True)
class CommitteeJudgment:
    """One committee's answer to one question, or the reason there is none.

    The smallest contract that is useful: who asked and under what
    terms, whether the question applied, the answer within that
    question, how much stands behind it, what it rests on, and — where
    there is no answer — which kind of no.

    **The contract travels with the judgment.** PR #113 passed it
    alongside, which left a seam where a caller could file a judgment
    under an identity it was not produced by; nothing checked, and a
    mis-filed judgment would have been indistinguishable from a real
    one. Carrying it here makes that unrepresentable.
    """

    asset: str

    #: Who judged, and under what terms. Persisted as an identity, so a
    #: record stays readable when this contract no longer exists.
    contract: CommitteeContract

    state: JudgmentState

    #: Whether the question was economically meaningful here at all —
    #: decided before any evidence was read, and carried rather than
    #: discarded because it is not recoverable from the rest.
    #:
    #: A verdict implies applicability; an abstention's *reason* implies
    #: it too. But an `UNAVAILABLE` judgment implies nothing, and
    #: inferring it would eventually collapse *we know this question does
    #: not apply* into *we do not know whether it applies* — the exact
    #: distinction that made BTC and TAO come out identical when their
    #: problems are opposite.
    basis: ApplicabilityBasis | None = None

    #: The answer, present exactly when `state` is JUDGED. **A token
    #: with a sentence, never a grade** — see `StructuralVerdict`.
    verdict: StructuralVerdict | None = None

    #: Established by code from the supporting evidence. Present with a
    #: verdict and meaningless without one.
    confidence: Confidence | None = None

    #: The findings the verdict rests on. Never empty for a judgment —
    #: a verdict that cites nothing is an opinion.
    refs: tuple[str, ...] = ()

    #: The eligible evidence this committee was actually given, and
    #: **empty wherever it reached an outcome without asking for any**.
    #:
    #: Carried on the judgment rather than fetched beside it, for the
    #: reason PR #113 removed the committee identity from `record_from`'s
    #: signature: *a value supplied alongside is a value that can
    #: disagree*. It did. The recording command read
    #: `committee.evidence(asset)` unconditionally while `judge()`
    #: returns before consulting anything when the question does not
    #: apply — so Bitcoin's Value Capture declined the question as the
    #: wrong instrument, cited nothing, and was recorded as having been
    #: given three findings it never saw.
    #:
    #: This is **not** `refs`. `refs` is what the verdict cited, and the
    #: corpus shows the two genuinely differ: eleven of twenty-six
    #: answered judgments cite fewer findings than they were given.
    #: Supplied and cited are two facts and this platform keeps both.
    considered: tuple[EligibleFinding, ...] = ()

    #: One sentence, grounded in those refs and validated like any other
    #: model output.
    because: str | None = None

    #: Why there is no verdict. Present exactly when ABSTAINED.
    abstained_because: AbstentionReason | None = None

    #: The worded reason there is no judgment at all. Present exactly
    #: when UNAVAILABLE.
    unavailable_because: str | None = None

    #: Why a drafted sentence was refused, where one was.
    #:
    #: **A prose failure is a presentation failure, not an analytical
    #: one.** A verdict that has already cleared its vocabulary and its
    #: grounding is a complete structural judgment; discarding it
    #: because the sentence beside it used a forbidden word threw away
    #: an answer the evidence supported. HYPE lost a judgment that way,
    #: and the loss was invisible until two committees sat side by side.
    #:
    #: The draft is still refused — the validator is untouched. What
    #: changes is that the refusal is recorded here instead of erasing
    #: the answer, and `because` falls back to the committee's own
    #: deterministic account.
    wording_refused: str | None = None

    judged_at: datetime | None = None
    model: str | None = None

    def __post_init__(self) -> None:
        # An answer outside the contract's own vocabulary would make the
        # fingerprint a description of something the record does not
        # contain — and longitudinal comparability rests on that
        # fingerprint meaning what it says.
        if self.verdict is not None and not self.contract.admits(self.verdict):
            raise ValueError(
                f"{self.contract.name} cannot answer {self.verdict.value!r}: "
                "it is not in the verdict vocabulary this committee's "
                "contract was fingerprinted from."
            )

    @property
    def applicability(self) -> Applicability | None:
        return self.basis.applicability if self.basis else None

    @property
    def economic_role(self) -> str | None:
        return self.basis.economic_role if self.basis else None

    @property
    def is_judged(self) -> bool:
        return self.state is JudgmentState.JUDGED

    @property
    def stated(self) -> str:
        """The answer in one line, whichever kind of answer it is."""

        if self.state is JudgmentState.JUDGED and self.verdict is not None:
            return f"{self.asset}: {self.verdict.stated}"

        if self.state is JudgmentState.ABSTAINED and self.abstained_because:
            return (
                f"{self.asset}: the committee abstained — "
                f"{self.abstained_because.stated}"
            )

        return (
            f"{self.asset}: no judgment is available — "
            f"{self.unavailable_because or 'the machinery did not run'}"
        )

    def grounded_in(self, eligible: set[str]) -> bool:
        """Whether every cited ref was actually supplied as eligible."""

        if self.state is not JudgmentState.JUDGED:
            return True

        return bool(self.refs) and set(self.refs) <= eligible


def abstain(
    asset: str,
    contract: CommitteeContract,
    reason: AbstentionReason,
    basis: ApplicabilityBasis | None = None,
    because: str | None = None,
    considered: tuple[EligibleFinding, ...] = (),
) -> CommitteeJudgment:
    """A committee that knows it cannot answer. A successful outcome.

    `because` defaults to the applicability reasoning, so a reader
    learns *why this question was the wrong instrument* rather than only
    that it was not answered.

    `considered` **defaults to nothing on purpose**. An applicability
    abstention is reached before any evidence is asked for, and it is the
    most common way to reach this function — so the default is the
    truthful value, and a caller that did consult evidence has to say so.
    The opposite default would restore the defect by omission.
    """

    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=JudgmentState.ABSTAINED,
        basis=basis,
        abstained_because=reason,
        because=because if because is not None else (basis.because if basis else None),
        considered=considered,
    )


def unavailable(
    asset: str,
    contract: CommitteeContract,
    because: str,
    basis: ApplicabilityBasis | None = None,
    considered: tuple[EligibleFinding, ...] = (),
) -> CommitteeJudgment:
    """No judgment, because the machinery failed. Not an abstention.

    The machinery can fail on either side of consulting the evidence, so
    `considered` is passed rather than assumed: a committee whose model
    was unreachable had already been given its findings, and one that
    never got that far had not.
    """

    return CommitteeJudgment(
        asset=asset,
        contract=contract,
        state=JudgmentState.UNAVAILABLE,
        basis=basis,
        unavailable_because=because,
        considered=considered,
    )


def confidence_from(
    supporting: int,
    across_captures: bool,
) -> Confidence:
    """How much stands behind a verdict, counted rather than judged.

    Deliberately a function of the evidence alone. It cannot see the
    verdict, and the verdict is chosen without seeing it — so more
    evidence raises confidence and never moves the answer, which is
    exactly what §7 asks to be demonstrated.
    """

    if across_captures:
        return Confidence.OBSERVED_OVER_TIME

    if supporting >= 2:
        return Confidence.MULTIPLE_OBSERVATIONS

    return Confidence.SINGLE_OBSERVATION
