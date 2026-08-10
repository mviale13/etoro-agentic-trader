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


class Remit(StrEnum):
    """The questions a committee may be assigned. One, for now.

    Deliberately not a taxonomy. The ruling's instruction was to choose
    the narrowest question the corpus already supports and build that
    one, rather than build a framework and then look for something to
    put in it — so this enumeration has a single member and will grow
    only when a second question is measured and earned.
    """

    #: Chosen by measurement rather than by preference. Fees are the
    #: widest non-price evidence in the corpus — 8 of 8 assets carry a
    #: reading — the holder-revenue sibling carries a figure for four
    #: and is established-and-empty for three, and the difference
    #: between those two absences is itself evidence under S2's sibling
    #: rule. Nothing else in the corpus separates six assets three ways
    #: on a question an investor would actually ask.
    VALUE_CAPTURE = "value_capture"

    @property
    def question(self) -> str:
        return _QUESTIONS[self]

    @property
    def stated(self) -> str:
        return _REMITS[self]


_REMITS = {Remit.VALUE_CAPTURE: "Value Capture Committee"}

#: The question, worded from what the evidence can actually settle.
#:
#: Two clauses, both of which must be evidenced, and neither of which is
#: a magnitude test. *Is there measured activity* is answered by the fee
#: reading; *is there an evidenced mechanism returning some of it* is
#: answered by the holder-revenue sibling and the provider's own
#: methodology sentence. What the question deliberately does **not**
#: ask is whether the amount is large enough to matter — six
#: observations do not establish a floor, and S5.3 already parked
#: magnitude outside quality for exactly this reason.
_QUESTIONS = {
    Remit.VALUE_CAPTURE: (
        "Does this network generate evidenced fee activity, and does an "
        "evidenced mechanism capture some of it for the token or its "
        "holders?"
    )
}


class Applicability(StrEnum):
    """Whether this question is economically meaningful for this asset.

    **The committee's own decision, in its own economic terms.** It
    reads the archetype layer as *evidence* and does not delegate to
    it — a distinction that matters because `TokenArchetype` was built
    to decide which questions an Asset Quality layer asks, and routing
    this committee's applicability through it would quietly make this
    committee a generic crypto-quality judgment wearing a narrow remit.

    Three states, and the third is the one a delegated rule loses.
    """

    #: The token's economic role includes capturing network activity, so
    #: asking whether it does is meaningful.
    APPLICABLE = "applicable"

    #: The token's economic role does not rest on capturing network
    #: fees, so the question is the wrong instrument. Bitcoin's fees are
    #: a security budget paid to miners — S5.3 established that the same
    #: issuance figure is a security budget or a transfer depending on
    #: where it goes, and the same is true of a fee. **An asset here is
    #: not judged adversely; it is not judged.**
    NOT_ECONOMICALLY_APPLICABLE = "not_economically_applicable"

    #: This platform cannot establish which of the two above is true —
    #: no archetype, or no mapped economic system. **Distinct from the
    #: second on purpose**: not knowing whether a question applies is
    #: not the same as knowing it does not.
    UNESTABLISHED = "unestablished"

    @property
    def is_applicable(self) -> bool:
        return self is Applicability.APPLICABLE


class Verdict(StrEnum):
    """The only answers to the remit. Two, and neither grades the asset.

    Scoped so tightly that the enumeration is the guard: no `BUY`, no
    `HOLD`, no `POSITIVE`, no `FAVOURABLE`, and no way to express a view
    about the asset as an investment.

    **Neither verdict is favourable or adverse**, and the naming says
    so. A mechanism being evidenced is a structural fact about the
    token's economics; whether it is *good* depends on what an investor
    is buying the asset for, and that judgment belongs to a layer that
    does not exist. The temptation to read `MECHANISM_EVIDENCED` as
    "good" is exactly the assumption this slice was told not to smuggle
    in.

    **Magnitude is not judged.** 64%, 18% and 9% are excellent contrast
    and six observations do not establish that 5% is a floor. S5.3 has
    already parked magnitude outside quality for the issuance case, and
    the same reasoning applies here: the committee reports the share as
    evidence and refuses to band it.
    """

    #: Activity is measured, and a mechanism routing some of it to the
    #: token or its holders is evidenced.
    MECHANISM_EVIDENCED = "mechanism_evidenced"

    #: Activity is measured, and the source establishes that no such
    #: mechanism exists — it publishes the holder-revenue figure for
    #: comparable entities and none here, which under S2's sibling rule
    #: is evidence of absence rather than absent evidence.
    NO_MECHANISM_EVIDENCED = "no_mechanism_evidenced"

    @property
    def stated(self) -> str:
        return {
            Verdict.MECHANISM_EVIDENCED: (
                "measured network activity is captured for the token by an "
                "evidenced mechanism"
            ),
            Verdict.NO_MECHANISM_EVIDENCED: (
                "measured network activity is not captured for the token, and "
                "the source establishes the absence rather than omitting it"
            ),
        }[self]


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

    The smallest contract that is useful: who asked, what was asked,
    the answer within that question, how much stands behind it, what it
    rests on, and — where there is no answer — which kind of no.
    """

    asset: str
    remit: Remit

    state: JudgmentState

    #: The answer, present exactly when `state` is JUDGED.
    verdict: Verdict | None = None

    #: Established by code from the supporting evidence. Present with a
    #: verdict and meaningless without one.
    confidence: Confidence | None = None

    #: The findings the verdict rests on. Never empty for a judgment —
    #: a verdict that cites nothing is an opinion.
    refs: tuple[str, ...] = ()

    #: One sentence, grounded in those refs and validated like any other
    #: model output.
    because: str | None = None

    #: Why there is no verdict. Present exactly when ABSTAINED.
    abstained_because: AbstentionReason | None = None

    #: The worded reason there is no judgment at all. Present exactly
    #: when UNAVAILABLE.
    unavailable_because: str | None = None

    judged_at: datetime | None = None
    model: str | None = None

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
    remit: Remit,
    reason: AbstentionReason,
    because: str | None = None,
) -> CommitteeJudgment:
    """A committee that knows it cannot answer. A successful outcome.

    `because` carries the committee's own economic reasoning, so a
    reader learns *why this question was the wrong instrument* rather
    than only that it was not answered.
    """

    return CommitteeJudgment(
        asset=asset,
        remit=remit,
        state=JudgmentState.ABSTAINED,
        abstained_because=reason,
        because=because,
    )


def unavailable(asset: str, remit: Remit, because: str) -> CommitteeJudgment:
    """No judgment, because the machinery failed. Not an abstention."""

    return CommitteeJudgment(
        asset=asset,
        remit=remit,
        state=JudgmentState.UNAVAILABLE,
        unavailable_because=because,
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
