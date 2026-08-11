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
`CommitteeIdentity` carries a fingerprint over the committee's question,
its applicability rule, its eligible-evidence contract and its verdict
vocabulary. Change any of them and two records stop being comparable —
reported as `INCOMPARABLE_VERSION` and compared no further, because a
transition computed across a redefinition is a fact about the
redefinition wearing the clothes of a fact about the asset.

**And nothing here is allowed to mean more than it says** — nor, since
the protocol was extracted, is it *able* to. A verdict reaches this
module as an opaque token with the committee's own sentence attached;
one answer becoming another is that transition and nothing else, and
this file could not tell you which of them was the favourable one if it
were asked. Those readings need a layer with explicit
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
    AbstentionReason,
    Applicability,
    CommitteeJudgment,
    Confidence,
    EligibleFinding,
    JudgmentState,
)
from app.domain.committee_protocol import CommitteeIdentity, Comparability
from app.domain.intelligence_journal import ObservationSpan

# ── the five states that must never collapse ────────────────────────


class JudgmentPosture(StrEnum):
    """Where a recorded judgment stood — without reading its verdict.

    The distinction the ruling protects, and the reason it needs
    protecting: four of these produce no verdict, and a history that
    stored *"no verdict"* would make them one fact. They are not one
    fact, and the transitions between them are the most informative
    thing this layer can report — *the question became answerable* and
    *the question turned out not to apply* are opposite readings of the
    same missing verdict.

    **Five rather than six, and the removed one is the finding.** PR
    #113 split the answered case into `EVIDENCE_OF_PRESENCE` and
    `EVIDENCE_OF_ABSENCE`, which required this module to read a Fee
    Capture verdict and decide what it meant. Measuring it showed the
    split was used for **wording only** — every decision in this file
    runs on `is_answered`, on verdict *identity*, on applicability and
    on contract comparability, and none of them ever asked which of the
    two it was.

    So the distinction did not need to be lost, only moved: a record
    carries its verdict token and the committee's own sentence for it,
    and *"answered `no_mechanism_evidenced`"* and *"answered
    `mechanism_evidenced`"* are as distinct as they ever were —
    distinguished by identity rather than by this file knowing which one
    is presence. A committee whose answers do not divide into presence
    and absence can now exist.
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

    #: The question applies and the committee gave one of its own
    #: answers. **Which answer is the verdict's business, not this
    #: enumeration's.**
    ANSWERED = "answered"

    @property
    def stated(self) -> str:
        return _POSTURES[self]

    @property
    def is_answered(self) -> bool:
        return self is JudgmentPosture.ANSWERED


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
    #: Deliberately incomplete on its own. The record appends the
    #: committee's own sentence for the verdict, because this module has
    #: no business finishing that sentence.
    JudgmentPosture.ANSWERED: "the question applies and the committee answered",
}


def posture_of(
    applicability: Applicability,
    state: JudgmentState,
    answered: bool,
) -> JudgmentPosture:
    """Which of the five a judgment stood in. Total, and never a default.

    Takes *whether* there is an answer, never the answer itself — the
    signature is the guard. A parameter typed as a verdict would invite
    exactly the branch this slice removed.

    Applicability is read first and on its own, because it is the
    question asked *before* any evidence, so an asset the question does
    not fit can never fall through into an evidence state and look like
    a gap.
    """

    if applicability is Applicability.UNESTABLISHED:
        return JudgmentPosture.APPLICABILITY_UNKNOWN

    if applicability is Applicability.NOT_ECONOMICALLY_APPLICABLE:
        return JudgmentPosture.KNOWN_NOT_APPLICABLE

    if state is JudgmentState.JUDGED and answered:
        return JudgmentPosture.ANSWERED

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
    committee: CommitteeIdentity

    #: When the committee reached it.
    judged_at: datetime

    #: When this record was written. Usually the same moment; kept apart
    #: because they answer different questions and a replayed record
    #: must not claim to be a fresh judgment.
    recorded_at: datetime

    applicability: Applicability
    state: JudgmentState

    #: The committee's own answer token, stored verbatim and never
    #: interpreted. A `str` rather than an enum on purpose: a record must
    #: stay readable when the committee that produced it has been
    #: reversioned or deleted, and reconstructing an enum member would
    #: mean this module holding a registry of what every committee's
    #: answers are called.
    verdict: str | None = None

    #: The committee's own sentence for that answer, quoted at the
    #: moment of judgment. **Quoting is not interpreting** — it is what
    #: lets this layer word an answer it is forbidden to understand, and
    #: it keeps yesterday's wording with yesterday's judgment.
    verdict_stated: str | None = None

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
                    self.committee.key,
                    str(self.committee.version),
                    self.committee.fingerprint,
                    self.judged_at.isoformat(),
                    self.applicability.value,
                    self.state.value,
                    self.verdict or "-",
                    self.confidence.value if self.confidence else "-",
                    self.evidence_digest,
                )
            ).encode()
        ).hexdigest()[:8]

        return f"{self.judged_at:%Y%m%dT%H%M%S}-{digest}"

    @property
    def posture(self) -> JudgmentPosture:
        return posture_of(self.applicability, self.state, self.verdict is not None)

    @property
    def answer(self) -> str:
        """The answer as the committee worded it, or its bare token.

        The fallback matters: a record written before wording was
        persisted still names *which* answer it was, and naming it is
        the whole of what this layer is allowed to do with it.
        """

        return self.verdict_stated or self.verdict or ""

    @property
    def stated(self) -> str:
        """What this record says, and nothing beyond it.

        Where there is an answer the sentence ends in the committee's
        own words. This module supplies *"the committee answered"* and
        stops — finishing that sentence would mean knowing what was
        answered.
        """

        if self.posture.is_answered and self.answer:
            return f"{self.asset}: {self.posture.stated} that {self.answer}"

        return f"{self.asset}: {self.posture.stated}"


def record_from(
    judgment: CommitteeJudgment,
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
        # Taken from the judgment rather than from a caller: an identity
        # supplied alongside is an identity that can disagree.
        committee=judgment.contract.identity,
        judged_at=judgment.judged_at or recorded_at,
        recorded_at=recorded_at,
        applicability=judgment.applicability,
        state=judgment.state,
        verdict=judgment.verdict.value if judgment.verdict else None,
        verdict_stated=judgment.verdict.stated if judgment.verdict else None,
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
    committee: str

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
                f"{self.current.stated}. The previous judgment was recorded "
                f"under {self.previous.committee.stated} and this one under "
                f"{self.current.committee.stated}, so the two are not "
                f"compared — {self.comparability.stated}."
            )

        if self.previous is None:
            return f"{self.current.stated}. This is {self.change.stated}."

        lines = [f"{self.current.stated}."]

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
            if previous.verdict == current.verdict
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

    committee = current.committee.key

    if previous is None:
        return JudgmentTransition(
            asset=current.asset,
            committee=committee,
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
            committee=committee,
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
        committee=committee,
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
    committee: str

    kind: StandingKind

    #: Today's judgment, whatever it concluded.
    current: JudgmentRecord

    #: The most recent comparable judgment that reached a verdict, where
    #: today's did not.
    previously: JudgmentRecord | None = None

    @property
    def verdict(self) -> str | None:
        """Today's answer, and only today's."""

        if self.kind is not StandingKind.CURRENT:
            return None

        return self.current.verdict

    @property
    def stated(self) -> str:
        if self.kind is StandingKind.CURRENT and self.current.verdict is not None:
            return f"{self.asset}: {self.current.answer}."

        if self.kind is StandingKind.PREVIOUS_NOT_REFRESHED and self.previously:
            return (
                f"{self.asset}: the previous judgment, on "
                f"{self.previously.judged_at:%-d %B %Y}, was that "
                f"{self.previously.answer}"
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

    committee = current.committee.key

    if current.posture.is_answered:
        return JudgmentStanding(
            asset=current.asset,
            committee=committee,
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
            committee=committee,
            kind=StandingKind.PREVIOUS_NOT_REFRESHED,
            current=current,
            previously=record,
        )

    return JudgmentStanding(
        asset=current.asset,
        committee=committee,
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
    committee: str
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
    committee: str,
    records: list[JudgmentRecord],
) -> JudgmentCoverage:
    """What the record can honestly say about its own reach."""

    if not records:
        return JudgmentCoverage(asset=asset, committee=committee)

    ordered = sorted(records, key=lambda record: record.judged_at)

    times = [record.judged_at for record in ordered]

    gaps = [later - earlier for earlier, later in zip(times, times[1:], strict=False)]

    return JudgmentCoverage(
        asset=asset,
        committee=committee,
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
