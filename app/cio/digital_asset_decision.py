"""The Artificial CIO's answer for a digital asset, from judged states only.

The gap this closes was measured twice. DV1 found the platform's two
crypto surfaces disagreeing about the same asset: the crypto dossier
holds the best-grounded evidence on the platform — settled supply
figures, two committees answered in their own vocabularies, honest
readiness arithmetic — and **no decision sentence at all**, while the
legacy executive surface still answered *INVESTIGATE, conviction 46*
from provider-fed signals the crypto rulings were built to replace.
An investor asking about Bitcoin was served knowledge without a verdict
on one page and a verdict without the knowledge on the other.

## What this consumes, and what it may never consume

The inputs are the two layers already addressed to an investment
consumer:

- **`AssetConsiderations`** — the Decision Bridge (#128), which carries
  each committee's conclusion with its posture, its own sentence, and
  the standing statement that its investment meaning is not established.
  This module is the bridge's first consumer that decides anything,
  which is what the bridge was built to make safe: a conclusion crosses,
  and what it is worth does not.
- **`InvestorAssessment`** (#117) — the strongest useful statement per
  subject, shaped, with every silence named.

Market context is structurally out of reach (S4's import guard covers
this package), and no provider payload is re-read here: everything
below is a judged or validated domain object.

## The rule, and why it is posture arithmetic

`digital-asset-gates@1` decides the state from **committee postures
alone** — never from a verdict's meaning, which this layer is forbidden
to know (#114: the framework may know that Committee X answered
question Y with verdict Z; it may never know what Z means). The
argument for each gate:

- **A question established as applicable is a direction research can
  take.** Whether it was answered (something is established to build
  on) or found evidence-insufficient (the missing evidence is named by
  the committee itself), the case merits research → INVESTIGATE.
- **An asset none of whose questions is even applicable yet cannot be
  investigated toward anything.** Where applicability itself is
  unestablished, this platform does not know *which questions to ask*,
  so research cannot be directed and the honest posture is to watch →
  MONITOR. The same holds where every question is known not to apply,
  and where no committee has recorded any judgment at all.
- **Nothing can pass INVESTIGATE.** This platform judges an investment
  case on business quality and valuation; a digital asset has neither
  to assess, no crypto quality band exists for any asset under the
  inherited quorum, and no committee conclusion has an established
  investment meaning. The ceiling is a statement about this platform.
- **Nothing reaches REJECT.** No crypto evidence layer licenses an
  adverse reading of a structural conclusion — a negative-sounding
  verdict is not a negative grade — so there is nothing a rejection
  could rest on. The branch does not exist rather than being guarded.

## Conviction

None, always, and structurally: DV2 ruled that a conviction is emitted
only where a decision cites support, and no crypto conclusion can be
cited as support because its investment meaning is unresolved by the
bridge's own (empty) licensing table. There is no numeric field to
fill, and the absence is worded rather than silent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.cio.decision_state import DecisionState
from app.cio.executive_decision import ExecutiveDecision
from app.domain.decision_rules import DIGITAL_ASSET_GATES, DecisionRule
from app.domain.investment_consideration import (
    AssetConsiderations,
    InvestmentConsideration,
)
from app.domain.investor_assessment import InvestorAssessment, StatementShape
from app.domain.judgment_history import JudgmentPosture

#: The postures under which a committee's question is established as
#: applicable to the asset — the states that make research *directable*,
#: whether or not an answer exists yet.
_APPLICABLE_POSTURES = frozenset(
    {
        JudgmentPosture.ANSWERED,
        JudgmentPosture.EVIDENCE_INSUFFICIENT,
        JudgmentPosture.EXECUTION_UNAVAILABLE,
    }
)


@dataclass(frozen=True, slots=True)
class UnresolvedQuestion:
    """One open question, in the words of the layer that owns it."""

    #: Who or what holds the question — a committee's name, or the
    #: assessment subject the statement is about.
    owner: str

    #: The owning layer's own account of what is open and why. Quoted,
    #: never composed here.
    stated: str


@dataclass(frozen=True, slots=True)
class DigitalAssetDecision:
    """One answer for one digital asset, worded from judged states.

    A projection, not a record: a deterministic function of recorded
    judgments and assessment statements, recomputable on every read.
    Nothing is stored and no journal event is written — a page view must
    never manufacture a judgment (#126's rule, kept).
    """

    symbol: str

    state: DecisionState

    #: Why this state, worded by the gate that selected it.
    rationale: str

    #: What the committees established, each line carrying the standing
    #: sentence that its investment meaning is not established. Quoted
    #: from the bridge — this layer neither reorders nor reweighs them.
    established: tuple[str, ...] = ()

    #: Questions established as the wrong instrument for this asset, in
    #: the committee's own words. **Never adverse**, and kept apart from
    #: `unresolved` because *does not apply* and *not yet answerable*
    #: are opposite readings of a missing answer.
    not_applicable: tuple[str, ...] = ()

    #: What is open, each in its owner's own words: committee questions
    #: awaiting evidence or applicability, assessment subjects held with
    #: too little to say, and subjects the assessment is silent about.
    unresolved: tuple[UnresolvedQuestion, ...] = ()

    #: Assessment statements whose shape is a real spread — material to
    #: an investor and stated as uncertainty, never as an adverse
    #: finding.
    material_uncertainties: tuple[str, ...] = ()

    #: Licensed adverse readings. Empty, and the emptiness is a finding:
    #: no crypto evidence layer licenses one. The absence is worded in
    #: `adverse_absent` so a surface never renders a bare empty list.
    adverse: tuple[str, ...] = ()

    adverse_absent: str = (
        "No crypto evidence layer licenses an adverse reading of a "
        "structural conclusion — a negative-sounding verdict is a "
        "structural fact, not a grade — so nothing is listed against "
        "this asset. Material uncertainties are stated as uncertainties."
    )

    #: Why no digital asset can currently progress past research. A
    #: statement about this platform, carried on every decision so the
    #: posture cannot be read as a view on the asset's merit.
    ceiling: str = (
        "No digital asset can currently progress past INVESTIGATE: this "
        "platform judges an investment case on business quality and "
        "valuation, a digital asset has neither to assess, and no "
        "committee conclusion has an established investment meaning. "
        "That is a limit of this platform, not a finding about the asset."
    )

    #: Why there is no number here, under DV2's rule.
    conviction_withheld_because: str = (
        "A conviction is emitted only where a decision cites support. "
        "No crypto conclusion can be cited as support — its investment "
        "meaning is not established — and no score exists for a digital "
        "asset, so no number is stated."
    )

    #: Registered committees with no recorded judgment, named so a thin
    #: corpus cannot read as a complete one.
    silent_committees: tuple[str, ...] = field(default=())

    #: Whether the reasoning system that judges this asset has anything to
    #: say about it — that is, whether any committee has recorded a
    #: judgment for it at all.
    #:
    #: **Not a measure of how much is known, and never a grade.** Both of
    #: TAO's committees recorded that they cannot establish whether their
    #: questions apply; that is an informed state reached by running, and
    #: it reads True. False is the one state in which this platform has
    #: not looked — no committee has concluded anything, so there is
    #: nothing for a surface to admit or an investor to read.
    #:
    #: It exists because the rationale already carried this distinction
    #: and carried it only in prose: *"No committee has recorded a
    #: judgment about this asset"*. A caller deciding whether the asset
    #: can be researched at all would otherwise have had to match on a
    #: sentence.
    judged: bool = False

    #: The named, versioned rule this decision was reached under —
    #: *produced under this exact rule*, never *this is the correct way
    #: to invest*. Same regime as the equity decision's `decided_under`.
    decided_under: tuple[DecisionRule, ...] = (DIGITAL_ASSET_GATES,)

    @property
    def conviction(self) -> None:
        """Always withheld. A property so nothing can ever set it."""

        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "state": self.state.value,
            "rationale": self.rationale,
            "established": list(self.established),
            "not_applicable": list(self.not_applicable),
            "unresolved": [
                {"owner": item.owner, "stated": item.stated} for item in self.unresolved
            ],
            "material_uncertainties": list(self.material_uncertainties),
            "adverse": list(self.adverse),
            "adverse_absent": self.adverse_absent,
            "ceiling": self.ceiling,
            # Deliberately no `conviction` key. The route guard forbids
            # that key anywhere in the crypto payload, and the guard is
            # right: a field that exists as null invites a number, and
            # no number can ever belong here. The worded absence is the
            # whole of what a surface may render.
            "conviction_withheld_because": self.conviction_withheld_because,
            "silent_committees": list(self.silent_committees),
            "judged": self.judged,
            "decided_under": [
                {"key": rule.key, "version": rule.version}
                for rule in self.decided_under
            ],
        }


def decide_digital_asset(
    considerations: AssetConsiderations,
    assessment: InvestorAssessment,
) -> DigitalAssetDecision:
    """`digital-asset-gates@1`: the state from postures, the words quoted.

    Deterministic and total. The same considerations and assessment
    produce the same decision, and every branch below tests a posture —
    never a verdict token, never a committee key, never a number.
    """

    items = considerations.considerations

    applicable = tuple(item for item in items if item.posture in _APPLICABLE_POSTURES)

    answered = tuple(item for item in items if item.posture.is_answered)

    state, rationale = _state_for(items, applicable, answered)

    return DigitalAssetDecision(
        symbol=considerations.asset,
        state=state,
        rationale=rationale,
        # A committee spoke, whatever it said — including that it cannot
        # tell whether its question applies.
        judged=bool(items),
        established=tuple(item.stated for item in answered),
        not_applicable=tuple(
            f"{item.committee.name}: {item.because or item.posture.stated}"
            for item in items
            if item.posture is JudgmentPosture.KNOWN_NOT_APPLICABLE
        ),
        unresolved=_unresolved(items, assessment),
        material_uncertainties=tuple(
            statement.stated
            for statement in assessment.statements
            if statement.shape is StatementShape.UNCERTAIN
        ),
        silent_committees=considerations.silent,
    )


def _state_for(
    items: tuple[InvestmentConsideration, ...],
    applicable: tuple[InvestmentConsideration, ...],
    answered: tuple[InvestmentConsideration, ...],
) -> tuple[DecisionState, str]:
    """Which state the postures reach, and the sentence that says why."""

    if not items:
        return (
            DecisionState.MONITOR,
            (
                "No committee has recorded a judgment about this asset, so "
                "nothing is established to research from. Convening the "
                "committees is the advance."
            ),
        )

    if not applicable:
        if any(item.posture is JudgmentPosture.APPLICABILITY_UNKNOWN for item in items):
            return (
                DecisionState.MONITOR,
                (
                    "No structural question is yet established as applicable "
                    "to this asset — this platform cannot say which questions "
                    "it should even be asked, so research cannot be directed. "
                    "Establishing the asset's economic role is the advance."
                ),
            )

        return (
            DecisionState.MONITOR,
            (
                "Every structural question this platform asks is established "
                "as the wrong instrument for this asset. That is knowledge, "
                "not an absence — and it leaves nothing to investigate with "
                "the instruments this platform currently has."
            ),
        )

    if answered:
        return (
            DecisionState.INVESTIGATE,
            (
                "Structural evidence is established and quoted below, and "
                "the case cannot progress past research: what these "
                "conclusions are worth to an investment case is not "
                "established by this platform."
            ),
        )

    return (
        DecisionState.INVESTIGATE,
        (
            "The structural questions apply and none is answered yet; the "
            "committees name the missing evidence below, which is what "
            "research would acquire."
        ),
    )


def _unresolved(
    items: tuple[InvestmentConsideration, ...],
    assessment: InvestorAssessment,
) -> tuple[UnresolvedQuestion, ...]:
    """Everything open, each entry in its owner's own words.

    Three sources, deliberately kept in one list: a committee that
    cannot yet answer, an assessment subject held with too little to
    say, and a subject the assessment is silent about are all questions
    an investor would want named — and the owner column says whose each
    one is.
    """

    open_questions: list[UnresolvedQuestion] = []

    for item in items:
        if item.posture in (
            JudgmentPosture.EVIDENCE_INSUFFICIENT,
            JudgmentPosture.EXECUTION_UNAVAILABLE,
            JudgmentPosture.APPLICABILITY_UNKNOWN,
        ):
            open_questions.append(
                UnresolvedQuestion(
                    owner=item.committee.name,
                    stated=item.because or item.posture.stated,
                )
            )

    for statement in assessment.statements:
        # A statement quoting a committee is that committee's fact under
        # a second owner — the consideration above already carries it
        # with the committee's own reason, and one fact under two owners
        # is the repetition the presentation-ownership audit measured.
        # `from_committee` is the provenance field built for exactly
        # this routing.
        if statement.shape is StatementShape.INSUFFICIENT:
            if statement.from_committee is not None:
                continue

            open_questions.append(
                UnresolvedQuestion(owner=statement.subject, stated=statement.stated)
            )

    committee_names = {item.committee.name for item in items}

    for subject in assessment.silent_about:
        # A committee silence is already carried above with the
        # committee's own reason; repeating it as a bare subject would
        # be the same fact twice under two owners.
        if subject in committee_names or subject in assessment.silent_committees:
            continue

        open_questions.append(
            UnresolvedQuestion(
                owner=subject,
                stated=(
                    f"This platform holds nothing useful about {subject.lower()} "
                    "for this asset, and says so rather than omitting the row."
                ),
            )
        )

    return tuple(open_questions)


def as_executive_decision(decision: DigitalAssetDecision) -> ExecutiveDecision:
    """The same judgment in the record shape every surface already reads.

    **A translation, never a second decision.** Nothing is computed here:
    the state, the rationale and every sentence are carried from the
    canonical answer above, and `decided_under` carries
    `digital-asset-gates@1` so a reader can establish which reasoning
    system produced the record. That stamp is the provenance — an
    executive record produced by the equity gates carries
    `decision-gates` and `conviction-mean` instead, and the two can
    never be confused for one another.

    **What is deliberately empty, and why.**

    - `key_strengths` and `key_risks`. A structural conclusion is not a
      strength. Both committee vocabularies say so in their own words —
      one documents its answers as structural facts and explicitly not
      favourable ones, the other states that its verdicts are
      deliberately not ordered — and the bridge's licensing table is
      empty besides. Filing a conclusion under *what argues for this
      security* would author the investment meaning that table refuses
      to grant, so both lists are empty and the rationale carries the
      meaning instead.
    - `conviction`. Withheld by construction, and there is no arithmetic
      here that could produce one.

    `evidence_weighed` is the neutral field — *whatever the signals
    measured, favourable or not* — so the committees' conclusions and
    their wrong-instrument findings both belong there, each still
    carrying its own clause. A wrong-instrument finding travelling as
    evidence weighed can never be read as an adverse one; travelling as
    a *risk* it inevitably would be.
    """

    return ExecutiveDecision(
        symbol=decision.symbol,
        state=decision.state,
        conviction=None,
        rationale=decision.rationale,
        # Conclusions and applicability findings, quoted. Neither is a
        # grade, and this is the one field that says so by not saying
        # otherwise.
        evidence_weighed=(*decision.established, *decision.not_applicable),
        key_strengths=(),
        key_risks=(),
        # What a later cycle could supply. An open question keeps its
        # owner's name, and a material spread is a reading that could be
        # settled — never an adverse finding about the asset.
        missing_evidence=(
            *(f"{item.owner}: {item.stated}" for item in decision.unresolved),
            *decision.material_uncertainties,
        ),
        decided_under=decision.decided_under,
    )
