"""What stands between an INVESTIGATE course and a capital decision.

`INVESTIGATE` ended in a description of missing evidence. This layer
turns it into a closed plan: one requirement per decision-critical
blocker, each naming what is missing, why it matters, what would
resolve it, and — the part the product was missing — **whether MOVRvest
can actually do anything about it**.

**Measured before it was built** (Stage 0, over the eight-asset corpus):

- The decision's blocker set is reproducible from three typed sources
  and nothing else, **exactly, 8 of 8**: committee assessments in a
  blocking state, assessment statements whose shape is `UNCERTAIN`, and
  the assessment's `silent_about` **minus** `silent_committees` — the
  domain already documents that subset relationship, so a silent
  committee is never counted twice. TAO is the case that forces it: its
  two silent subjects *are* its two committees.
- **Not one watch item resolves any blocker, anywhere.** 7 blockers, 10
  watch items, **0** connections. The two vocabularies cannot meet by
  construction: a blocker's refs are source names (`CoinGecko`) and
  committee keys (`supply_governance`), and a watch item's are metric
  refs (`network.fees.hyperliquid-protocol`, `flow.30d`). HYPE's
  fee-economy item standing beside three unrelated supply blockers was
  not a HYPE defect — it is the corpus-wide state. So a requirement is
  derived from **the blocker**, and a watch item is contextual evidence
  that resolves nothing.
- `not_economically_applicable` is **never** a blocker. BTC's Value
  Capture committee abstains on it, and the wrong instrument for a
  question is not a gap in the evidence.

**No cadence, no threshold, no promise.** Nothing here says when an
observation will arrive, how many readings would be enough, or what a
resolved blocker would produce. Resolving one licenses reconsideration
and nothing more.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.cio.digital_asset_decision import DigitalAssetDecision
from app.domain.committee_matrix import AssetCommitteeMatrix
from app.domain.investor_assessment import InvestorAssessment, StatementShape
from app.domain.mechanical_issuance import MechanicalIssuance
from app.domain.supply_semantics import SupplyPicture

#: Abstentions that are a gap in the evidence. `not_economically_applicable`
#: is deliberately absent: a question that is the wrong instrument for an
#: asset is answered, not blocked, and listing it would invent a defect.
BLOCKING_ABSTENTIONS = frozenset(
    {"insufficient_evidence", "applicability_unestablished"}
)

#: Which supply concept backs each assessment subject, for reading the
#: methodology-disclosure flags behind a conflict. Keyed on the domain's
#: own subject strings, which the assessment layer owns.
_SUBJECT_CONCEPT = {
    "Tokens in existence": "emitted_supply",
    "Circulating supply": "circulating_estimate",
    "Maximum supply": "max_supply",
}


class NextStepKind(StrEnum):
    """What MOVRvest can do about a blocker. **Not a grade.**

    Two members, because two are what the live corpus produces. The
    brief that commissioned this layer offered six candidates and the
    measurement produced `NOT_CURRENTLY_RESOLVABLE` six times and
    `CONVENE_COMMITTEE` once — so `NEXT_COMPARABLE_OBSERVATION`,
    `RECONCILE_HELD_EVIDENCE`, `TARGETED_PRIMARY_RESEARCH`,
    `OWNER_RULING` and `CAPABILITY_MISSING` are **measured and not
    declared**. This repository's standing rule is that a vocabulary
    member is observed before it is named; a member nothing can produce
    is a promise, and this layer exists to stop the product making
    those.

    What each of the undeclared ones would need is written down in
    `RESEARCH_PLAN.md` rather than reserved here.
    """

    #: An existing MOVRvest workflow would produce the answer: the
    #: committee holds its evidence and simply has not been convened.
    CONVENE_COMMITTEE = "convene_committee"

    #: MOVRvest has no automatic path to this evidence today. **A
    #: statement about this platform, never about the asset.**
    NOT_CURRENTLY_RESOLVABLE = "not_currently_resolvable"

    @property
    def stated(self) -> str:
        return _KINDS[self]


_KINDS = {
    NextStepKind.CONVENE_COMMITTEE: "An existing MOVRvest workflow can answer this",
    NextStepKind.NOT_CURRENTLY_RESOLVABLE: (
        "MOVRvest has no automatic path to this today"
    ),
}


@dataclass(frozen=True, slots=True)
class ResearchRequirement:
    """One blocker, and the truthful next step for it."""

    #: The blocker's typed identity — a committee key or an assessment
    #: subject. What the one-to-one rule is checked against.
    blocker: str

    #: The owning layer's own name for it.
    blocker_stated: str

    #: What is missing, quoted from the layer that established it.
    what_is_missing: str

    #: Why an investor should care — a licensed meaning where the
    #: assessment carries one, otherwise the committee's own question.
    #: Never worded here.
    why_it_matters: str

    #: What would settle it. Quoted, or counted from typed flags.
    resolution_needed: str

    next_step_kind: NextStepKind

    #: What MOVRvest can do, said plainly. Never a promise, never a
    #: schedule, and never a claim about what resolving it would yield.
    next_step_stated: str

    #: Whether repeating an existing MOVRvest workflow could change
    #: this. False is not a verdict on the asset.
    retryable: bool

    #: The view where this requirement can be inspected, where one
    #: genuinely helps.
    destination: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "blocker": self.blocker,
            "blocker_stated": self.blocker_stated,
            "what_is_missing": self.what_is_missing,
            "why_it_matters": self.why_it_matters,
            "resolution_needed": self.resolution_needed,
            "next_step_kind": self.next_step_kind.value,
            "next_step_kind_stated": self.next_step_kind.stated,
            "next_step_stated": self.next_step_stated,
            "retryable": self.retryable,
            "destination": self.destination,
        }


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    """Every decision-critical blocker, each with exactly one requirement."""

    symbol: str

    #: True exactly when the course asks for no capital action. Read
    #: from the decision's own ceiling, never decided here.
    asks_for_capital: bool

    requirements: tuple[ResearchRequirement, ...] = ()

    #: Why there is nothing to plan, where there is nothing.
    absent_because: str | None = None

    #: What resolving a blocker licenses — and it is never a
    #: recommendation.
    reconsideration: str = (
        "When decision-critical evidence changes, MOVRvest can reconsider "
        "the case. Resolving a requirement licenses another look; it does "
        "not produce a recommendation, a purchase, a capital envelope or a "
        "higher conviction."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "asks_for_capital": self.asks_for_capital,
            "requirements": [item.as_dict() for item in self.requirements],
            "absent_because": self.absent_because,
            "reconsideration": self.reconsideration,
        }


def _committee_requirement(cell: Any) -> ResearchRequirement:
    """A committee that could not answer, or was not convened.

    The two are opposite states and the wording separates them: one is
    an evidence gap this platform cannot close today, the other is a
    judgment MOVRvest can run over evidence it already holds.
    """

    state = getattr(cell.state, "value", cell.state)
    missing = cell.because or cell.unavailable_because or cell.stated

    if state == "unavailable":
        return ResearchRequirement(
            blocker=cell.committee.key,
            blocker_stated=cell.committee.name,
            what_is_missing=missing,
            why_it_matters=cell.question,
            resolution_needed="A recorded judgment over the evidence already held.",
            next_step_kind=NextStepKind.CONVENE_COMMITTEE,
            next_step_stated=(
                "Convening this committee is an existing MOVRvest workflow, "
                "and the evidence beneath it is unchanged."
            ),
            retryable=True,
            destination="evidence",
        )

    return ResearchRequirement(
        blocker=cell.committee.key,
        blocker_stated=cell.committee.name,
        what_is_missing=missing,
        why_it_matters=cell.question,
        # **Not the question again.** `why_it_matters` already quotes it,
        # and rendering "An answer to: <question>" beside it printed the
        # same sentence twice in one row.
        resolution_needed="Evidence this committee accepts as an answer.",
        next_step_kind=NextStepKind.NOT_CURRENTLY_RESOLVABLE,
        next_step_stated="No MOVRvest workflow can obtain this evidence today.",
        retryable=False,
        destination="evidence",
    )


def _supply_requirement(
    statement: Any,
    supply: SupplyPicture | None,
) -> ResearchRequirement:
    """A quantity two sources report differently.

    **The count comes from typed flags, never from the prose.** S4.6's
    `SupplyMethodology.disclosed` says, per source and per concept,
    whether the vendor publishes what its figure excludes — and an
    undisclosed methodology is not a different methodology, it is an
    unexplained one. Where any source publishes none, the difference
    cannot be settled from what MOVRvest holds, and no amount of
    re-reading held evidence changes that.
    """

    concept = _SUBJECT_CONCEPT.get(statement.subject)

    sources = [
        fact
        for fact in (supply.facts if supply is not None else ())
        if concept is not None and fact.concept.value == concept
    ]
    undisclosed = [fact for fact in sources if not fact.methodology.disclosed]

    if sources and undisclosed:
        resolution = (
            f"An exclusion set from the {len(undisclosed)} of {len(sources)} "
            "sources that publish none."
        )
        step = (
            f"{len(undisclosed)} of {len(sources)} sources publish no "
            "exclusion set, so the difference cannot be settled from held "
            "evidence."
        )
    else:
        resolution = "What each source includes and excludes from its figure."
        step = "No MOVRvest workflow can obtain this evidence today."

    return ResearchRequirement(
        blocker=statement.subject,
        blocker_stated=statement.subject,
        what_is_missing=statement.uncertainty or statement.stated,
        why_it_matters=(
            statement.why_it_matters[0].stated
            if statement.why_it_matters
            else statement.stated
        ),
        resolution_needed=resolution,
        next_step_kind=NextStepKind.NOT_CURRENTLY_RESOLVABLE,
        next_step_stated=step,
        retryable=False,
        destination="tokenomics",
    )


def _silent_requirement(subject: str, stated: str) -> ResearchRequirement:
    """A subject the assessment holds nothing about at all."""

    return ResearchRequirement(
        blocker=subject,
        blocker_stated=subject,
        what_is_missing=stated,
        why_it_matters=(
            "The assessment has nothing to say about this subject, so no "
            "question that depends on it can be answered."
        ),
        resolution_needed=f"Any usable reading of {subject.lower()}.",
        next_step_kind=NextStepKind.NOT_CURRENTLY_RESOLVABLE,
        next_step_stated="No MOVRvest workflow can obtain this evidence today.",
        retryable=False,
        destination="tokenomics",
    )


def research_plan(
    decision: DigitalAssetDecision,
    assessment: InvestorAssessment,
    matrix: AssetCommitteeMatrix,
    supply: SupplyPicture | None,
    issuance: MechanicalIssuance | None,
) -> ResearchPlan:
    """One requirement per decision-critical blocker. No more, no fewer.

    `issuance` is accepted and deliberately **not used to word a next
    step**. `IssuanceRuleProvider.rule()` is a hard-coded three-symbol
    allowlist that returns a bare `None` for everything else, and its
    docstring reads that `None` as *an allocation-release token has no
    rule to read*. The corpus falsifies that: TAO's own developments
    record *"Bittensor (TAO) First Halving Reduces Block Rewards and
    Daily Issuance"*, so a mechanical rule plainly exists and `None`
    means only that this platform has not read one. **Absence of a rule
    and absence of a reader are opposite claims**, and until the
    provider distinguishes them nothing here may say which it is.
    """

    requirements: list[ResearchRequirement] = []

    for cell in matrix.assessments:
        state = getattr(cell.state, "value", cell.state)
        because = str(cell.abstained_because or "")

        if state == "unavailable" or because in BLOCKING_ABSTENTIONS:
            requirements.append(_committee_requirement(cell))

    for statement in assessment.statements:
        if statement.shape is StatementShape.UNCERTAIN:
            requirements.append(_supply_requirement(statement, supply))

    # `silent_committees` is documented as a subset of `silent_about`,
    # so subtracting it is how a silent committee avoids being counted
    # twice — TAO's two silent subjects *are* its two committees.
    silent_committees = set(assessment.silent_committees)

    for subject in assessment.silent_about:
        if subject in silent_committees:
            continue

        stated = next(
            (item.stated for item in decision.unresolved if item.owner == subject),
            f"This platform holds nothing useful about {subject.lower()}.",
        )

        requirements.append(_silent_requirement(subject, stated))

    return ResearchPlan(
        symbol=decision.symbol,
        asks_for_capital=not decision.ceiling,
        requirements=tuple(requirements),
        absent_because=None
        if requirements
        else (
            "No decision-critical evidence is currently open for this asset. "
            "The course still rests on the platform boundary recorded under "
            "Evidence."
        ),
    )
