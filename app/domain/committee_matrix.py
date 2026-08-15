"""What the registered committees have concluded about one asset.

A projection of independent judgments, and **not a new judge**. It
answers one question — *what have the committees concluded?* — by
placing each committee's own answer beside the others without combining
them, comparing them, or learning what any of them means.

**The shape was measured rather than designed.** Reading the live
two-committee records field by field showed which parts of a judgment
both implementations always produce, which parts only look shared, and
which cannot be compared at all:

```text
always, both committees   asset, contract, judged_at, applicability,
                          state, evidence digest and count
present only when answered
                          verdict, its sentence, confidence, refs
present only when not     abstention reason, the committee's own
                          sentence, the unavailable reason
syntactically shared,     evidence_count — Fee Capture's 11 for HYPE
semantically not          counts fee readings; Supply Governance's 11
                          for ADA counts rule parameters
demonstrably incomparable confidence — Supply Governance saturates at
                          MULTIPLE_OBSERVATIONS for 8, 9 and 11 findings
```

So the cell carries everything and combines nothing. **Confidence is
carried and never compared**, because the measurement says it is
calibrated to one committee's evidence shape. `evidence_count` is
carried per committee and never summed, because counting two different
kinds of thing produces a number about neither.

**There is no aggregate here and no room for one.** No score, no vote,
no agreement, no weight, no rank, no favourable/adverse mapping, and no
common verdict scale. Two committees answering different structural
questions are not two votes on a shared proposition, and the layer that
decides what a collection of judgments means for an investor is
deliberately not this one.

**Identical-looking absences keep their reasons.** Four assets read
"unanswered" across this corpus for four different causes, and the cell
keeps each committee's own sentence precisely so a surface cannot
flatten them into *unknown*.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.domain.committee_judgment import (
    AbstentionReason,
    Applicability,
    Confidence,
    JudgmentState,
)
from app.domain.committee_protocol import CommitteeIdentity, Comparability
from app.domain.judgment_history import (
    EvidenceSemantics,
    JudgmentPosture,
    JudgmentRecord,
)


@dataclass(frozen=True, slots=True)
class CommitteeAssessment:
    """One committee's standing conclusion about one asset. One cell.

    Everything a reader needs to understand *this* committee's answer,
    and nothing that relates it to any other committee's. The absence of
    a relating field is the design: a cell that carried a
    `relative_to_others` of any kind would be the aggregation layer
    wearing a projection's name.
    """

    asset: str

    #: Who concluded it, and under what contract — carried from the
    #: record rather than from today's registry, so a conclusion reached
    #: under an earlier contract still says so.
    committee: CommitteeIdentity

    #: The question this committee owns, as it words it. Absent when the
    #: committee that wrote the record is no longer registered: a record
    #: outlives its code, and inventing a question for it would be worse
    #: than saying nothing.
    question: str | None

    #: Where the judgment stood, without reading the verdict.
    posture: JudgmentPosture

    applicability: Applicability
    state: JudgmentState

    #: The committee's own answer token and its own sentence for it.
    #: Present exactly when answered, and **never interpreted here**.
    verdict: str | None = None
    verdict_stated: str | None = None

    #: Why there is no answer. Three fields because they fail
    #: differently: the enumerated reason, the committee's own sentence,
    #: and the worded machinery failure.
    abstained_because: AbstentionReason | None = None
    because: str | None = None
    unavailable_because: str | None = None

    #: Where a drafted sentence was refused. Carried because it changes
    #: what can be said *about the explanation* while leaving the answer
    #: exactly as it was — a prose failure is a presentation failure.
    wording_refused: str | None = None

    #: As this committee currently expresses it. **Carried, never
    #: compared** — see the module docstring.
    confidence: Confidence | None = None

    #: The refs the answer cited and how much eligible evidence stood
    #: behind it, in this committee's own units.
    #:
    #: **Two facts, not one rounded off.** The corpus settles that they
    #: are distinct: eleven of twenty-six answered judgments cite fewer
    #: findings than they were given. Neither is derivable from the
    #: other and neither is comparable across committees.
    refs: tuple[str, ...] = ()
    evidence_count: int = 0

    #: What `evidence_count` was counting when this record was written.
    #: Carried so a surface can word the count truthfully for a record
    #: that predates the correction, rather than restating an old
    #: measurement in today's terms.
    evidence_semantics: EvidenceSemantics = EvidenceSemantics.HELD_AT_RECORDING

    #: The established economic role at the time of judgment, where one
    #: was established.
    economic_role: str | None = None

    judged_at: datetime | None = None

    #: Whether the contract this was concluded under is still the live
    #: one. `None` where the committee is no longer registered, which is
    #: a third state and not a failure.
    comparability: Comparability | None = None

    #: How many judgments this committee has recorded for this asset. A
    #: count, and — the journal's rule, inherited — never a duration.
    judgments_recorded: int = 0

    @property
    def is_answered(self) -> bool:
        return self.posture.is_answered

    @property
    def answer(self) -> str:
        """The answer in the committee's own words, or its bare token."""

        return self.verdict_stated or self.verdict or ""

    @property
    def stated(self) -> str:
        """This cell in one line, built from the committee's own words.

        The framework supplies the posture and the committee finishes
        the sentence. Nothing here decides what the answer means.
        """

        if self.is_answered and self.answer:
            return f"{self.posture.stated} that {self.answer}"

        if self.because:
            return f"{self.posture.stated} — {self.because}"

        if self.unavailable_because:
            return f"{self.posture.stated} — {self.unavailable_because}"

        return self.posture.stated

    @property
    def is_current_contract(self) -> bool:
        """Whether this conclusion was reached under today's contract."""

        return self.comparability is Comparability.COMPARABLE

    def as_dict(self) -> dict[str, Any]:
        """A serialisable cell, for a surface that renders and nothing more.

        **Every semantic decision is already made here.** The frontend
        receives states and sentences, never the raw material to infer a
        verdict's meaning, an applicability, a confidence or a
        combination — which is the standing rule that the dashboard
        presents and never calculates.
        """

        return {
            "asset": self.asset,
            "committee": {
                "key": self.committee.key,
                "name": self.committee.name,
                "version": self.committee.version,
                "fingerprint": self.committee.fingerprint,
                "stated": self.committee.stated,
            },
            "question": self.question,
            "posture": self.posture.value,
            "posture_stated": self.posture.stated,
            "answered": self.is_answered,
            "applicability": self.applicability.value,
            "state": self.state.value,
            "verdict": self.verdict,
            "verdict_stated": self.verdict_stated,
            "abstained_because": (
                self.abstained_because.value if self.abstained_because else None
            ),
            "because": self.because,
            "unavailable_because": self.unavailable_because,
            "wording_refused": self.wording_refused,
            "confidence": self.confidence.value if self.confidence else None,
            "confidence_stated": (self.confidence.stated if self.confidence else None),
            "refs": list(self.refs),
            "evidence_count": self.evidence_count,
            "evidence_semantics": self.evidence_semantics.value,
            "evidence_semantics_stated": self.evidence_semantics.stated,
            "economic_role": self.economic_role,
            "judged_at": self.judged_at.isoformat() if self.judged_at else None,
            "comparability": (self.comparability.value if self.comparability else None),
            "comparability_stated": (
                self.comparability.stated if self.comparability else None
            ),
            "is_current_contract": self.is_current_contract,
            "judgments_recorded": self.judgments_recorded,
            "stated": self.stated,
        }


def assessment_from(
    record: JudgmentRecord,
    question: str | None,
    comparability: Comparability | None,
    judgments_recorded: int,
) -> CommitteeAssessment:
    """Project one recorded judgment into one cell. Nothing is derived.

    Every field is copied. The projection adds three things a record
    cannot know on its own — the live question, whether the contract is
    still current, and how many judgments precede this one — and none of
    them touches what the answer means.
    """

    return CommitteeAssessment(
        asset=record.asset,
        committee=record.committee,
        question=question,
        posture=record.posture,
        applicability=record.applicability,
        state=record.state,
        verdict=record.verdict,
        verdict_stated=record.verdict_stated,
        abstained_because=record.abstained_because,
        because=record.because,
        unavailable_because=record.unavailable_because,
        wording_refused=record.wording_refused,
        confidence=record.confidence,
        refs=record.refs,
        evidence_count=record.evidence_count,
        evidence_semantics=record.evidence_semantics,
        economic_role=record.economic_role,
        judged_at=record.judged_at,
        comparability=comparability,
        judgments_recorded=judgments_recorded,
    )


@dataclass(frozen=True, slots=True)
class UnjudgedCommittee:
    """A registered committee that has concluded nothing about this asset.

    Its own type, because *this committee has never run here* and *this
    committee ran and could not answer* are different facts and a matrix
    that rendered them alike would be claiming the first had been tried.
    """

    asset: str
    committee: CommitteeIdentity
    question: str

    @property
    def stated(self) -> str:
        return (
            "this committee has recorded no judgment for this asset, so "
            "nothing is known about what it would conclude"
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "committee": {
                "key": self.committee.key,
                "name": self.committee.name,
                "version": self.committee.version,
                "fingerprint": self.committee.fingerprint,
                "stated": self.committee.stated,
            },
            "question": self.question,
            "posture": None,
            "answered": False,
            "judgments_recorded": 0,
            "stated": self.stated,
        }


@dataclass(frozen=True, slots=True)
class AssetCommitteeMatrix:
    """Every registered committee's conclusion about one asset.

    A row, and deliberately only a row. It offers no summary of itself:
    there is no `overall`, no `consensus`, no `agreement`, no `score`
    and no way to ask how many committees answered *as though that
    number meant something* — the count below is a rendering aid and
    says so.
    """

    asset: str

    assessments: tuple[CommitteeAssessment, ...] = ()

    #: Committees that are registered and have concluded nothing here.
    unjudged: tuple[UnjudgedCommittee, ...] = ()

    @property
    def answered(self) -> tuple[CommitteeAssessment, ...]:
        """The cells carrying an answer. **Not a score of any kind.**

        Exposed because a surface renders answered and unanswered cells
        differently, and for no other reason. Counting them and calling
        the count a strength is the exact move this layer refuses.
        """

        return tuple(cell for cell in self.assessments if cell.is_answered)

    def for_committee(self, key: str) -> CommitteeAssessment | None:
        for cell in self.assessments:
            if cell.committee.key == key:
                return cell

        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "asset": self.asset,
            "committees": [cell.as_dict() for cell in self.assessments]
            + [cell.as_dict() for cell in self.unjudged],
        }
