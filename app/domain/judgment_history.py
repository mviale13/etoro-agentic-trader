"""What one committee concluded, when, and what changed since.

The journal remembers *evidence*. This remembers *judgment*, and the two
are not the same memory. A number moving is not a conclusion moving, and
the whole reason this layer exists is that a system holding both will
otherwise report the first as the second — which is the most expensive
sentence an investment platform can write, because it is the one a
reader acts on.

So the separation is structural rather than careful:

```text
JudgmentChange      what happened to the committee's answer
SupportChange       what happened to the count of evidence beneath it
EvidenceMovement    what happened to the evidence itself
```

Three axes on every transition, never one field. **Evidence moving while
the answer stands still is the ordinary case**, and it renders as an
unchanged verdict with moved evidence — not as news.

**A historical verdict is evidence of what the committee concluded then.**
It is not today's verdict, and `JudgmentStanding` is the object that
refuses to let it become one: when today's committee cannot answer, the
standing carries `previously` and its `verdict` property returns
`None`. A caller cannot print a stale verdict as current by accident,
because there is no field that offers it as current.

**A verdict means what its committee's contract made it mean.**
`CommitteeVersion` carries a fingerprint over the remit question, the
applicability rule, the eligible-evidence contract and the verdict
vocabulary. Change any of them and two records stop being comparable —
reported as `INCOMPARABLE_VERSION` and compared no further, because a
transition computed across a redefinition is a fact about the
redefinition wearing the clothes of a fact about the asset.

**And nothing here is allowed to mean more than it says.**
`NO_MECHANISM_EVIDENCED → MECHANISM_EVIDENCED` is that transition and
nothing else: not an improvement, not a strengthened case, not a
development worth acting on. Those readings need a layer with explicit
permission to make them, and no such layer exists. The wording in this
module is built only from the enumerations below, never from free text
supplied elsewhere, so the vocabulary is finite and checkable — and a
test checks it.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum

from app.domain.committee_judgment import (
    ELIGIBLE_CLAIM_TYPES,
    AbstentionReason,
    Applicability,
    CommitteeJudgment,
    Confidence,
    EligibleFinding,
    JudgmentState,
    Remit,
    Verdict,
)
from app.domain.intelligence_journal import ObservationSpan

# ── the committee's identity ────────────────────────────────────────


def fingerprint_of(
    question: str,
    applicability_rule: str,
    eligible: frozenset[str],
    verdicts: tuple[str, ...],
) -> str:
    """A digest over everything that gives a verdict its meaning.

    Four inputs, and each one is a way a verdict can silently change
    meaning while keeping its name: the question it answers, the rule
    deciding whether that question applies, the evidence admitted to it,
    and the vocabulary of the answer itself.

    Derived rather than declared, so it cannot drift from the code. A
    record persists the fingerprint it was produced under; comparing it
    with today's live one is what makes §6 structural instead of
    remembered.
    """

    payload = "|".join(
        (
            question.strip(),
            applicability_rule.strip(),
            ",".join(sorted(eligible)),
            ",".join(sorted(verdicts)),
        )
    )

    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def eligible_contract() -> frozenset[str]:
    """The claim types a committee may see, as the fingerprint sees them."""

    return frozenset(claim.value for claim in ELIGIBLE_CLAIM_TYPES)


def verdict_vocabulary() -> tuple[str, ...]:
    """Every answer the committee can give, as the fingerprint sees it."""

    return tuple(verdict.value for verdict in Verdict)


@dataclass(frozen=True, slots=True)
class CommitteeVersion:
    """Which committee produced a judgment, and under what contract.

    The version number is the declaration a human reads; the fingerprint
    is what a comparison actually trusts. They are both carried because
    they fail differently — a forgotten version bump is caught by the
    fingerprint, and a fingerprint that happens to survive a meaning
    change is caught by the reviewer who had to bump the number.
    """

    remit: Remit
    version: int
    fingerprint: str

    @property
    def stated(self) -> str:
        return f"{self.remit.stated} v{self.version}"

    def comparability(self, other: CommitteeVersion) -> Comparability:
        """Whether a judgment under this contract may be compared with one
        under the other's."""

        if self.remit is not other.remit:
            return Comparability.DIFFERENT_REMIT

        if self.version != other.version:
            return Comparability.DIFFERENT_VERSION

        if self.fingerprint != other.fingerprint:
            return Comparability.CONTRACT_CHANGED

        return Comparability.COMPARABLE


class Comparability(StrEnum):
    """Whether two judgments answer the same question in the same terms.

    §6. The two failures are told apart deliberately: a bumped version
    is somebody declaring a change, and a changed fingerprint under an
    unchanged version is a change nobody declared. The second is a
    defect in this platform and saying so is more useful than treating
    them as one.
    """

    COMPARABLE = "comparable"

    #: A different question entirely.
    DIFFERENT_REMIT = "different_remit"

    #: The committee was versioned, so its verdicts may not mean the
    #: same thing. Declared, and therefore honest.
    DIFFERENT_VERSION = "different_version"

    #: Same declared version, different contract. Nobody bumped the
    #: number, and the fingerprint noticed.
    CONTRACT_CHANGED = "contract_changed"

    @property
    def is_comparable(self) -> bool:
        return self is Comparability.COMPARABLE

    @property
    def stated(self) -> str:
        return {
            Comparability.COMPARABLE: (
                "both judgments were produced under the same committee contract"
            ),
            Comparability.DIFFERENT_REMIT: (
                "the two judgments answer different questions, so neither "
                "says anything about the other"
            ),
            Comparability.DIFFERENT_VERSION: (
                "the committee was versioned between them, so a verdict "
                "produced under the earlier version may not mean what the "
                "same word means now"
            ),
            Comparability.CONTRACT_CHANGED: (
                "the committee's contract changed without its version "
                "changing, so the two are not compared and this platform "
                "cannot say what the earlier verdict meant"
            ),
        }[self]


# ── the five states that must never collapse ────────────────────────


class JudgmentPosture(StrEnum):
    """Where a recorded judgment actually stood. §2, made total.

    The distinction the ruling protects, and the reason it needs
    protecting: four of these produce no verdict, and a history that
    stored *"no verdict"* would make them one fact. They are not one
    fact, and the transitions between them are the most informative
    thing this layer can report — *the question became answerable* and
    *the question turned out not to apply* are opposite readings of the
    same missing verdict.

    Six rather than five, because the committee already refuses to
    collapse the last two: an abstention is the committee knowing its
    limits and an unavailable judgment is the machinery failing, and
    reporting a broken provider as intellectual honesty is exactly the
    lie `JudgmentState` was built to prevent.
    """

    #: The question is the wrong instrument for this asset. **Never
    #: adverse**, and a surface must not render it as a missing answer.
    KNOWN_NOT_APPLICABLE = "known_not_applicable"

    #: This platform cannot establish whether the question applies.
    APPLICABILITY_UNKNOWN = "applicability_unknown"

    #: The question applies and the eligible evidence cannot answer it.
    EVIDENCE_INSUFFICIENT = "evidence_insufficient"

    #: The question applies, evidence exists, and the machinery that
    #: judges did not run. A fact about this platform, not the asset.
    EXECUTION_UNAVAILABLE = "execution_unavailable"

    #: The question applies and the answer is that no mechanism is
    #: evidenced — evidence of absence, not absent evidence.
    EVIDENCE_OF_ABSENCE = "evidence_of_absence"

    #: The question applies and the answer is that a mechanism is
    #: evidenced.
    EVIDENCE_OF_PRESENCE = "evidence_of_presence"

    @property
    def stated(self) -> str:
        return _POSTURES[self]

    @property
    def is_answered(self) -> bool:
        return self in (
            JudgmentPosture.EVIDENCE_OF_ABSENCE,
            JudgmentPosture.EVIDENCE_OF_PRESENCE,
        )


_POSTURES = {
    JudgmentPosture.KNOWN_NOT_APPLICABLE: (
        "the question is not economically meaningful for this asset, so it "
        "was left unanswered rather than answered"
    ),
    JudgmentPosture.APPLICABILITY_UNKNOWN: (
        "this platform could not establish whether the question applies to "
        "this asset at all"
    ),
    JudgmentPosture.EVIDENCE_INSUFFICIENT: (
        "the question applies and the eligible evidence could not answer it"
    ),
    JudgmentPosture.EXECUTION_UNAVAILABLE: (
        "the question applies and the committee did not run, so there is no "
        "answer either way"
    ),
    JudgmentPosture.EVIDENCE_OF_ABSENCE: (
        "the question applies and the committee answered that no mechanism is evidenced"
    ),
    JudgmentPosture.EVIDENCE_OF_PRESENCE: (
        "the question applies and the committee answered that a mechanism is evidenced"
    ),
}


def posture_of(
    applicability: Applicability,
    state: JudgmentState,
    verdict: Verdict | None,
) -> JudgmentPosture:
    """Which of the six a judgment stood in. Total, and never a default.

    Applicability is read first and on its own, because it is the
    question asked *before* any evidence — so an asset the question does
    not fit can never fall through into an evidence state and look like
    a gap.
    """

    if applicability is Applicability.UNESTABLISHED:
        return JudgmentPosture.APPLICABILITY_UNKNOWN

    if applicability is Applicability.NOT_ECONOMICALLY_APPLICABLE:
        return JudgmentPosture.KNOWN_NOT_APPLICABLE

    if state is JudgmentState.JUDGED and verdict is not None:
        return (
            JudgmentPosture.EVIDENCE_OF_PRESENCE
            if verdict is Verdict.MECHANISM_EVIDENCED
            else JudgmentPosture.EVIDENCE_OF_ABSENCE
        )

    if state is JudgmentState.UNAVAILABLE:
        return JudgmentPosture.EXECUTION_UNAVAILABLE

    return JudgmentPosture.EVIDENCE_INSUFFICIENT


# ── the record ──────────────────────────────────────────────────────


def evidence_digest_of(findings: tuple[EligibleFinding, ...]) -> str:
    """A digest over the evidence a committee was given.

    Over the findings' refs *and* their wording, so a figure moving
    inside an unchanged ref is a changed digest. That is the whole point:
    without it, *"the same three findings"* would look identical whether
    or not the numbers in them had moved, and §4's first case could not
    be demonstrated at all.
    """

    payload = "|".join(
        sorted(f"{finding.ref}={finding.stated}" for finding in findings)
    )

    return hashlib.sha256(payload.encode()).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class JudgmentRecord:
    """One committee judgment, as it stood. Immutable, forever.

    **The judgment event, never a recommendation.** There is no field
    here for conviction, for a portfolio action, for an overall view, or
    for a score, and there is deliberately no field for the synthesis
    prose either — a model's reading of a judgment is communication, and
    persisting it would turn last week's wording into this week's
    history.
    """

    asset: str
    committee: CommitteeVersion

    #: When the committee reached it.
    judged_at: datetime

    #: When this record was written. Usually the same moment; kept apart
    #: because they answer different questions and a replayed record
    #: must not claim to be a fresh judgment.
    recorded_at: datetime

    applicability: Applicability
    state: JudgmentState

    verdict: Verdict | None = None
    confidence: Confidence | None = None

    #: The refs the verdict cited.
    refs: tuple[str, ...] = ()

    #: A digest over every eligible finding supplied, and how many there
    #: were. The evidence axis rests on these.
    evidence_digest: str = ""
    evidence_count: int = 0

    abstained_because: AbstentionReason | None = None

    #: Worded, because the ways machinery fails are not enumerable. Never
    #: composed into a transition sentence — free text from elsewhere
    #: would put vocabulary this layer does not control into a statement
    #: about change.
    unavailable_because: str | None = None

    #: The established economic role at the time of judgment, where one
    #: was established. What lets a changed applicability be attributed
    #: to a changed understanding rather than reported as unexplained.
    economic_role: str | None = None

    model: str | None = None

    @property
    def record_id(self) -> str:
        """A stable handle a transition can cite.

        Derived from content, so re-recording the same judgment at the
        same moment is recognisably the same event rather than a second
        one.
        """

        digest = hashlib.sha256(
            "|".join(
                (
                    self.asset,
                    self.committee.remit.value,
                    str(self.committee.version),
                    self.committee.fingerprint,
                    self.judged_at.isoformat(),
                    self.applicability.value,
                    self.state.value,
                    self.verdict.value if self.verdict else "-",
                    self.confidence.value if self.confidence else "-",
                    self.evidence_digest,
                )
            ).encode()
        ).hexdigest()[:8]

        return f"{self.judged_at:%Y%m%dT%H%M%S}-{digest}"

    @property
    def posture(self) -> JudgmentPosture:
        return posture_of(self.applicability, self.state, self.verdict)

    @property
    def stated(self) -> str:
        """What this record says, and nothing beyond it."""

        return f"{self.asset}: {self.posture.stated}"


def record_from(
    judgment: CommitteeJudgment,
    committee: CommitteeVersion,
    evidence: tuple[EligibleFinding, ...],
    recorded_at: datetime,
) -> JudgmentRecord:
    """Turn one committee output into the event that is kept.

    Refuses a judgment whose applicability the committee did not state.
    `Applicability.UNESTABLISHED` is a *known* state — this platform
    established that it cannot tell — and a judgment that never said
    would be recorded as that known state and become a lie about what
    was checked. So it raises instead.
    """

    if judgment.applicability is None:
        raise ValueError(
            "a judgment with no stated applicability cannot be recorded: "
            "not knowing whether a question applies is itself a state, and "
            "it must not be inferred from silence."
        )

    return JudgmentRecord(
        asset=judgment.asset,
        committee=committee,
        judged_at=judgment.judged_at or recorded_at,
        recorded_at=recorded_at,
        applicability=judgment.applicability,
        state=judgment.state,
        verdict=judgment.verdict,
        confidence=judgment.confidence,
        refs=judgment.refs,
        evidence_digest=evidence_digest_of(evidence),
        evidence_count=len(evidence),
        abstained_because=judgment.abstained_because,
        unavailable_because=judgment.unavailable_because,
        economic_role=judgment.economic_role,
        model=judgment.model,
    )


# ── the three axes ──────────────────────────────────────────────────


class JudgmentChange(StrEnum):
    """What happened to the committee's answer. §3, and only §3.

    Every member describes the *answer*. None of them describes the
    asset, the evidence, or what anyone should conclude — those are the
    other two axes and a layer that does not exist.
    """

    #: Nothing precedes it.
    FIRST_JUDGMENT = "first_judgment"

    #: The same answer as before.
    VERDICT_UNCHANGED = "verdict_unchanged"

    #: A different answer from before.
    VERDICT_CHANGED = "verdict_changed"

    #: No answer before, an answer now.
    BECAME_ANSWERABLE = "became_answerable"

    #: An answer before, none now. **Never a reversal** — the previous
    #: answer was not contradicted, it was not refreshed.
    BECAME_UNANSWERABLE = "became_unanswerable"

    #: Whether the question applies is now established and was not.
    APPLICABILITY_ESTABLISHED = "applicability_established"

    #: Whether the question applies is not what it was.
    APPLICABILITY_CHANGED = "applicability_changed"

    #: No answer then, no answer now.
    STILL_UNANSWERED = "still_unanswered"

    #: The contract changed, so the two are not compared at all.
    INCOMPARABLE_VERSION = "incomparable_version"

    @property
    def stated(self) -> str:
        return _CHANGES[self]

    @property
    def is_verdict_movement(self) -> bool:
        """Whether the committee's answer itself moved.

        False for an unchanged verdict whatever the evidence did, which
        is the property §4 turns on.
        """

        return self in (
            JudgmentChange.VERDICT_CHANGED,
            JudgmentChange.BECAME_ANSWERABLE,
            JudgmentChange.BECAME_UNANSWERABLE,
        )


_CHANGES = {
    JudgmentChange.FIRST_JUDGMENT: (
        "the first judgment this committee has recorded for this asset"
    ),
    JudgmentChange.VERDICT_UNCHANGED: (
        "the committee reached the same answer as at the previous comparable judgment"
    ),
    JudgmentChange.VERDICT_CHANGED: (
        "the committee reached a different answer from the previous comparable judgment"
    ),
    JudgmentChange.BECAME_ANSWERABLE: (
        "the committee answered a question it could not answer at the "
        "previous comparable judgment"
    ),
    JudgmentChange.BECAME_UNANSWERABLE: (
        "the committee could not answer a question it answered at the "
        "previous comparable judgment, which leaves the earlier answer "
        "unrefreshed rather than contradicted"
    ),
    JudgmentChange.APPLICABILITY_ESTABLISHED: (
        "whether this question applies to this asset is now established, "
        "and was not at the previous comparable judgment"
    ),
    JudgmentChange.APPLICABILITY_CHANGED: (
        "whether this question applies to this asset is not what it was at "
        "the previous comparable judgment"
    ),
    JudgmentChange.STILL_UNANSWERED: (
        "the committee reached no answer, as at the previous comparable judgment"
    ),
    JudgmentChange.INCOMPARABLE_VERSION: (
        "the two judgments were produced under different committee "
        "contracts and are not compared"
    ),
}


class SupportChange(StrEnum):
    """What happened to the count of evidence beneath the answer.

    **A count, never a grade.** `confidence_from` counts independent
    supporting observations and cannot see the verdict; this counts the
    difference between two of those counts and cannot see it either. So
    more support is *more observations*, and reading it as a firmer
    conclusion is exactly the inflation §7 forbids — the wording below
    says observations for that reason and says nothing else.
    """

    INCREASED = "increased"
    DECREASED = "decreased"
    UNCHANGED = "unchanged"

    #: One side has no confidence at all, because one side has no
    #: verdict. Confidence is meaningless without one and is not
    #: compared across that boundary.
    NOT_COMPARABLE = "not_comparable"

    @property
    def stated(self) -> str:
        return {
            SupportChange.INCREASED: (
                "more independent observations stand behind the answer than "
                "at the previous judgment"
            ),
            SupportChange.DECREASED: (
                "fewer independent observations stand behind the answer than "
                "at the previous judgment"
            ),
            SupportChange.UNCHANGED: (
                "the same amount of independent observation stands behind "
                "the answer as at the previous judgment"
            ),
            SupportChange.NOT_COMPARABLE: (
                "one of the two judgments reached no answer, so the support "
                "beneath them is not compared"
            ),
        }[self]


class EvidenceMovement(StrEnum):
    """What happened to the evidence itself. The axis §4 exists for.

    Separate from `JudgmentChange` on purpose and forever. Evidence
    moving is the ordinary case — a fee reading is different every day —
    and a platform that reported every moved number as a moved
    conclusion would be wrong almost every time it spoke.
    """

    #: Byte-identical eligible evidence.
    UNCHANGED = "unchanged"

    #: The eligible evidence is not what it was. **Not a conclusion
    #: about the asset**, and on its own not a change in anything the
    #: committee decided.
    CHANGED = "changed"

    #: Eligible evidence exists where there was none.
    ARRIVED = "arrived"

    #: No eligible evidence is held where there was some. A fact about
    #: what this platform can currently read.
    WITHDRAWN = "withdrawn"

    #: Not compared, because the contracts differ.
    NOT_COMPARABLE = "not_comparable"

    @property
    def stated(self) -> str:
        return {
            EvidenceMovement.UNCHANGED: (
                "the eligible evidence is identical to the previous judgment's"
            ),
            EvidenceMovement.CHANGED: (
                "the eligible evidence is not identical to the previous judgment's"
            ),
            EvidenceMovement.ARRIVED: (
                "eligible evidence is held where the previous judgment had none"
            ),
            EvidenceMovement.WITHDRAWN: (
                "no eligible evidence is held where the previous judgment had some"
            ),
            EvidenceMovement.NOT_COMPARABLE: (
                "the two judgments were produced under different committee "
                "contracts, so their evidence is not compared"
            ),
        }[self]

    @property
    def moved(self) -> bool:
        return self in (
            EvidenceMovement.CHANGED,
            EvidenceMovement.ARRIVED,
            EvidenceMovement.WITHDRAWN,
        )


# ── the transition ──────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class JudgmentTransition:
    """What code can establish about two recorded judgments.

    Deterministic and complete before any model is asked anything. §8's
    order is the whole design: **the model explains the transition, it
    does not discover it**, and it cannot discover it because it is
    handed this object already decided.

    The schema has three change fields, two records and a sentence.
    There is no field for a recommendation, a sentiment, a portfolio
    action or an overall view, and adding one would mean editing this
    file with the reason written down.
    """

    asset: str
    remit: Remit

    comparability: Comparability

    change: JudgmentChange
    support: SupportChange
    evidence: EvidenceMovement

    current: JudgmentRecord
    previous: JudgmentRecord | None = None

    #: The records this rests on. Never empty — a transition that cannot
    #: be checked against the record is not one.
    record_ids: tuple[str, ...] = ()

    @property
    def stated(self) -> str:
        """The transition in one paragraph, built only from enumerations.

        Composed from `stated` properties and record fields, never from
        free text supplied by a committee or a provider. That is what
        keeps the vocabulary of this layer finite, and finite is what
        makes §7 checkable rather than promised.
        """

        if not self.comparability.is_comparable and self.previous is not None:
            # The refusal is stated, not left to be inferred from two
            # version numbers. A reader who sees an old verdict and a new
            # one side by side will read a change into them unless the
            # sentence says there is none to read.
            return (
                f"{self.asset}: {self.current.posture.stated}. The previous "
                f"judgment was recorded under {self.previous.committee.stated} "
                f"and this one under {self.current.committee.stated}, so the "
                f"two are not compared — {self.comparability.stated}."
            )

        if self.previous is None:
            return (
                f"{self.asset}: {self.current.posture.stated}. This is "
                f"{self.change.stated}."
            )

        lines = [f"{self.asset}: {self.current.posture.stated}."]

        lines.append(f"Compared with the previous judgment, {self.change.stated}.")

        if self.change is JudgmentChange.APPLICABILITY_CHANGED:
            lines.append(_role_sentence(self.previous, self.current))

        if self.support is not SupportChange.NOT_COMPARABLE:
            lines.append(f"{self.support.stated.capitalize()}.")

        lines.append(f"{self.evidence.stated.capitalize()}.")

        if self.evidence.moved and not self.change.is_verdict_movement:
            lines.append(
                "The evidence moved and the committee's answer did not, "
                "which is a fact about the evidence and not a change in "
                "what the committee concluded."
            )

        return " ".join(lines)

    @property
    def is_grounded(self) -> bool:
        return bool(self.record_ids)


def _role_sentence(previous: JudgmentRecord, current: JudgmentRecord) -> str:
    """Why applicability moved, where the record can say.

    The honest branch is the second. Applicability is decided from the
    established economic role, so a changed applicability over an
    unchanged role is a change this platform cannot account for — and
    saying so is more useful than a sentence that implies it can.
    """

    if previous.economic_role != current.economic_role:
        return (
            f"The established economic role changed from "
            f"{previous.economic_role or 'none established'} to "
            f"{current.economic_role or 'none established'}, which is what "
            "decides whether this question applies."
        )

    return (
        "The established economic role did not change, so this platform "
        "cannot account for the difference."
    )


def _support_change(
    previous: JudgmentRecord,
    current: JudgmentRecord,
) -> SupportChange:
    """Two confidence states compared, where comparing them means anything.

    Confidence without a verdict is meaningless — the committee says so
    — so a boundary with no verdict on one side is `NOT_COMPARABLE`
    rather than a fabricated equality.
    """

    if previous.confidence is None or current.confidence is None:
        return SupportChange.NOT_COMPARABLE

    if current.confidence.rank > previous.confidence.rank:
        return SupportChange.INCREASED

    if current.confidence.rank < previous.confidence.rank:
        return SupportChange.DECREASED

    return SupportChange.UNCHANGED


def _evidence_movement(
    previous: JudgmentRecord,
    current: JudgmentRecord,
) -> EvidenceMovement:
    if not previous.evidence_count and current.evidence_count:
        return EvidenceMovement.ARRIVED

    if previous.evidence_count and not current.evidence_count:
        return EvidenceMovement.WITHDRAWN

    if previous.evidence_digest == current.evidence_digest:
        return EvidenceMovement.UNCHANGED

    return EvidenceMovement.CHANGED


def _change(previous: JudgmentRecord, current: JudgmentRecord) -> JudgmentChange:
    """Which single fact best describes the move. Precedence, not scoring.

    Applicability is tested before anything about verdicts, because it
    is the question asked before any evidence and it *explains* the
    verdict states beneath it. A question that stopped applying has not
    become unanswerable — it has stopped being asked, and those are
    different findings about an asset.
    """

    if previous.applicability is not current.applicability:
        if previous.applicability is Applicability.UNESTABLISHED:
            return JudgmentChange.APPLICABILITY_ESTABLISHED

        return JudgmentChange.APPLICABILITY_CHANGED

    answered_before = previous.posture.is_answered
    answered_now = current.posture.is_answered

    if answered_before and answered_now:
        return (
            JudgmentChange.VERDICT_UNCHANGED
            if previous.verdict is current.verdict
            else JudgmentChange.VERDICT_CHANGED
        )

    if answered_now:
        return JudgmentChange.BECAME_ANSWERABLE

    if answered_before:
        return JudgmentChange.BECAME_UNANSWERABLE

    return JudgmentChange.STILL_UNANSWERED


def compare(
    current: JudgmentRecord,
    previous: JudgmentRecord | None = None,
) -> JudgmentTransition:
    """State what changed between two judgments. No model, ever.

    Incomparability short-circuits everything. A verdict transition
    computed across a redefinition would be arithmetic over two
    different questions, and presenting it as a finding about the asset
    is precisely the confusion §6 exists to prevent — so the other two
    axes are set to `NOT_COMPARABLE` rather than computed and hedged.
    """

    remit = current.committee.remit

    if previous is None:
        return JudgmentTransition(
            asset=current.asset,
            remit=remit,
            comparability=Comparability.COMPARABLE,
            change=JudgmentChange.FIRST_JUDGMENT,
            support=SupportChange.NOT_COMPARABLE,
            evidence=EvidenceMovement.NOT_COMPARABLE,
            current=current,
            record_ids=(current.record_id,),
        )

    comparability = current.committee.comparability(previous.committee)

    ids = (previous.record_id, current.record_id)

    if not comparability.is_comparable:
        return JudgmentTransition(
            asset=current.asset,
            remit=remit,
            comparability=comparability,
            change=JudgmentChange.INCOMPARABLE_VERSION,
            support=SupportChange.NOT_COMPARABLE,
            evidence=EvidenceMovement.NOT_COMPARABLE,
            current=current,
            previous=previous,
            record_ids=ids,
        )

    return JudgmentTransition(
        asset=current.asset,
        remit=remit,
        comparability=comparability,
        change=_change(previous, current),
        support=_support_change(previous, current),
        evidence=_evidence_movement(previous, current),
        current=current,
        previous=previous,
        record_ids=ids,
    )


def transitions(records: list[JudgmentRecord]) -> tuple[JudgmentTransition, ...]:
    """Every consecutive pair, oldest first. Deterministic."""

    ordered = sorted(records, key=lambda record: record.judged_at)

    if not ordered:
        return ()

    found = [compare(ordered[0])]

    found.extend(
        compare(later, earlier)
        for earlier, later in zip(ordered, ordered[1:], strict=False)
    )

    return tuple(found)


# ── what may be said today ──────────────────────────────────────────


class StandingKind(StrEnum):
    """Whether the committee's answer is current, and if not, what is.

    §5, and the middle member is the whole point. A previous verdict is
    evidence of what the committee concluded then; it is never today's
    conclusion, and the difference between *"the mechanism remains
    evidenced"* and *"the previous judgment was that a mechanism is
    evidenced, and today's evidence cannot refresh it"* is the
    difference between a claim and a record.
    """

    #: Today's committee answered.
    CURRENT = "current"

    #: Today's committee did not answer, and a comparable earlier
    #: judgment did. The earlier answer is reported as history and never
    #: restated as a finding.
    PREVIOUS_NOT_REFRESHED = "previous_not_refreshed"

    #: Today's committee did not answer, and nothing comparable
    #: preceded it.
    NONE = "none"


@dataclass(frozen=True, slots=True)
class JudgmentStanding:
    """What this platform may say about this committee's view right now.

    **`verdict` is `None` unless today's committee reached one.** Not a
    convention — the property is the enforcement, and a caller wanting
    the earlier answer must reach through `previously`, whose name says
    what it is. A stale verdict cannot be printed as current by
    accident because nothing offers it as current.
    """

    asset: str
    remit: Remit

    kind: StandingKind

    #: Today's judgment, whatever it concluded.
    current: JudgmentRecord

    #: The most recent comparable judgment that reached a verdict, where
    #: today's did not.
    previously: JudgmentRecord | None = None

    @property
    def verdict(self) -> Verdict | None:
        """Today's answer, and only today's."""

        if self.kind is not StandingKind.CURRENT:
            return None

        return self.current.verdict

    @property
    def stated(self) -> str:
        if self.kind is StandingKind.CURRENT and self.current.verdict is not None:
            return f"{self.asset}: {self.current.verdict.stated}."

        if self.kind is StandingKind.PREVIOUS_NOT_REFRESHED and self.previously:
            return (
                f"{self.asset}: the previous judgment, on "
                f"{self.previously.judged_at:%-d %B %Y}, was that "
                f"{self.previously.verdict.stated if self.previously.verdict else ''}"
                f". Today {self.current.posture.stated}. The earlier answer is "
                "therefore reported as what the committee concluded then, and "
                "is not restated as a current finding."
            )

        return f"{self.asset}: {self.current.posture.stated}."


def standing(
    current: JudgmentRecord,
    history: list[JudgmentRecord],
) -> JudgmentStanding:
    """Today's answer, or the honest account of not having one.

    Searches backwards for the most recent judgment that both reached a
    verdict *and* was produced under a comparable contract. An earlier
    verdict under an incomparable contract cannot be reported as what
    the committee previously concluded, because nobody can say what it
    would have concluded under this one.
    """

    remit = current.committee.remit

    if current.posture.is_answered:
        return JudgmentStanding(
            asset=current.asset,
            remit=remit,
            kind=StandingKind.CURRENT,
            current=current,
        )

    ordered = sorted(history, key=lambda record: record.judged_at)

    for record in reversed(ordered):
        if record.record_id == current.record_id:
            continue

        if not record.posture.is_answered:
            continue

        if not current.committee.comparability(record.committee).is_comparable:
            continue

        return JudgmentStanding(
            asset=current.asset,
            remit=remit,
            kind=StandingKind.PREVIOUS_NOT_REFRESHED,
            current=current,
            previously=record,
        )

    return JudgmentStanding(
        asset=current.asset,
        remit=remit,
        kind=StandingKind.NONE,
        current=current,
    )


# ── coverage ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class JudgmentCoverage:
    """How often this committee has actually judged this asset.

    The journal's hardest rule, inherited without softening: **a count
    of judgments is not a duration of committee coverage.** Three
    judgments across three weeks are three judgments, and a sentence
    saying *"the committee has found this for three weeks"* claims a
    continuity nobody performed. So the wording says judgments, names
    the span, and names the longest gap inside it.
    """

    asset: str
    remit: Remit
    span: ObservationSpan | None = None
    versions: tuple[str, ...] = field(default_factory=tuple)

    @property
    def stated(self) -> str:
        if self.span is None:
            return (
                f"{self.asset}: this committee has recorded no judgment for "
                "this asset, so nothing can be said about how its view has "
                "moved."
            )

        if self.span.count == 1:
            return (
                f"{self.asset}: one recorded judgment, on "
                f"{self.span.last_at:%-d %B %Y}. One judgment describes a "
                "moment and not a history."
            )

        days = max(self.span.span.days, 0)

        window = f" spanning {days} day(s)" if days else " on the same day"

        gap = self.span.largest_gap.days

        hole = f", the longest gap between them {gap} day(s)" if gap >= 2 else ""

        contracts = (
            f" Produced under {len(self.versions)} committee contracts."
            if len(self.versions) > 1
            else ""
        )

        return (
            f"{self.asset}: {self.span.count} recorded judgments{window}"
            f"{hole}. That is a count of judgments and not a duration of "
            f"continuous review.{contracts}"
        )


def coverage(
    asset: str,
    remit: Remit,
    records: list[JudgmentRecord],
) -> JudgmentCoverage:
    """What the record can honestly say about its own reach."""

    if not records:
        return JudgmentCoverage(asset=asset, remit=remit)

    ordered = sorted(records, key=lambda record: record.judged_at)

    times = [record.judged_at for record in ordered]

    gaps = [later - earlier for earlier, later in zip(times, times[1:], strict=False)]

    return JudgmentCoverage(
        asset=asset,
        remit=remit,
        span=ObservationSpan(
            count=len(ordered),
            first_at=times[0],
            last_at=times[-1],
            largest_gap=max(gaps) if gaps else timedelta(0),
        ),
        versions=tuple(
            sorted({record.committee.stated for record in ordered}),
        ),
    )
