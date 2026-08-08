"""The canonical investment decision — what the platform may conclude.

The object `docs/architecture/INVESTMENT_DECISION.md` (accepted
2026-08-08) froze. Every future reasoning engine produces this object
and nothing else, the way every reader produces observations and
nothing else. A decision resolves disagreement, never uncertainty:
uncertainty is inherited from the facts at its narrowest width
(`rests_on`), disagreement between implications is adjudicated by a
named rule with the losing implications preserved (`weighed`), and
what the inputs cannot support is a refusal that says why.

The shape enforces the accepted properties rather than trusting an
engine to honour them: a decision that answers no question, states a
clause without edges, attaches an action to anything but RECOMMEND,
or reaches INVESTIGATE on the research-spend question cannot be
constructed at all.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.domain.agreement import Agreement
from app.domain.provenance import Provenance


class DecisionQuestion(StrEnum):
    """What a decision is an answer to.

    The vocabulary is closed at four for v1 and grows only when a real
    case and a deterministic rule table earn another question (§19a).
    Exit remains the limiting case of decrease-to-zero until a real
    case demonstrates that it needs different semantics.
    """

    ENTRY = "entry"
    INCREASE = "increase"
    DECREASE = "decrease"
    RESEARCH_SPEND = "research_spend"


class DecisionVerdict(StrEnum):
    """The constitutional postures toward a question (constitution §10)."""

    REJECT = "reject"
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    PREPARE = "prepare"
    RECOMMEND = "recommend"


@dataclass(frozen=True, slots=True)
class Clause:
    """One structural statement, carrying its evidence-graph edges.

    A clause that cannot name its edges cannot be stated — which is
    how "refuses unsupported conclusions" becomes a shape instead of a
    virtue.
    """

    states: str

    #: References into the decision's basis, e.g. "policy:target.stocks=60%".
    rests_on: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.states.strip():
            raise ValueError("a clause must state something")
        if not self.rests_on:
            raise ValueError("a clause that cannot name its edges cannot be stated")


@dataclass(frozen=True, slots=True)
class Clauses:
    """The Executive Brief's three questions, answered structurally.

    Communication words these; it never adds, strengthens, or softens
    them (constitution §11).
    """

    what_changed: Clause
    why_it_matters: Clause
    why_for_this_investor: Clause


@dataclass(frozen=True, slots=True)
class Implication:
    """One course an input implied, and whether it prevailed.

    The disagreement record preserves what lost the way a consensus
    preserves its minority answers — adjudicated, never erased.
    """

    course: str
    because: str
    rests_on: tuple[str, ...]
    prevailed: bool


@dataclass(frozen=True, slots=True)
class EstablishedFacts:
    """The verified-chain part of the basis, by reference.

    Only these are facts in this platform's sense: they passed
    identity, grounding, applicability and consensus.
    """

    #: The filing, as an investor would cite it.
    source: str

    consensus_state: str
    observation_count: int
    quorum: int
    reading: Provenance

    #: The claims consumed, verbatim references.
    facts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ContextObservation:
    """A context input: provider-reported, uncalibrated, labelled.

    Never presented as filing-grade established knowledge. Absent with
    its reason when unavailable or not consumed by the deciding rule.
    """

    kind: str
    observed_at: datetime | None
    facts: tuple[str, ...]
    absent_because: str | None

    def __post_init__(self) -> None:
        if self.absent_because is not None and self.facts:
            raise ValueError("a context observation is consumed or absent, never both")
        if self.absent_because is None and not self.facts:
            raise ValueError("an absent context must carry its reason")


@dataclass(frozen=True, slots=True)
class DeclaredPolicy:
    """The investor's instruction — authority, not evidence.

    The one input the decision obeys rather than weighs, cited by the
    version it was decided under.
    """

    version: str
    clauses: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Refusal:
    """No verdict, with the refusing layer's reason verbatim.

    A refusal is never neutral in effect — refusing entry leaves the
    investor out, refusing decrease leaves the investor in — which is
    why it is question-scoped like every decision.
    """

    because: str

    def __post_init__(self) -> None:
        if not self.because.strip():
            raise ValueError("a refusal must carry its reason")


@dataclass(frozen=True, slots=True)
class InvestmentDecision:
    """One answer to one question about one subject, on a recorded basis.

    An append-only event: superseded by a later decision in the same
    (subject, question) stream, never revised. The current stance is
    derived — the latest non-superseded answer per question — never
    stored as another source of truth.
    """

    decision_id: str
    subject: str
    question: DecisionQuestion
    decided_at: datetime

    #: What occasioned the decision, worded (open vocabulary), and the
    #: changed facts it names, by reference.
    occasion: str
    occasioned_by: tuple[str, ...]

    #: The basis, in three kinds that never blend. Facts and policy are
    #: absent-with-reason where unavailable; contexts carry their own
    #: absence wording.
    facts: EstablishedFacts | None
    facts_because: str | None
    portfolio: ContextObservation
    market: ContextObservation
    policy: DeclaredPolicy | None
    policy_because: str | None

    #: The outcome: exactly one of verdict and refusal.
    verdict: DecisionVerdict | None
    refusal: Refusal | None

    #: RECOMMEND only: the question's affirmative made executable, as
    #: policy-room arithmetic — never a target the platform invented.
    action: str | None

    #: INVESTIGATE only: the question it raised.
    raises: DecisionQuestion | None

    #: Present exactly when there is a verdict.
    clauses: Clauses | None

    #: The implications weighed, losers preserved.
    weighed: tuple[Implication, ...]

    #: The named deterministic rule that produced the outcome.
    decided_by: str

    #: The narrowest consumed consensus agreement — the decision's
    #: firmness is this field; there is no other. Absent with its
    #: reason where no consensus claim was consumed.
    rests_on: Agreement | None
    rests_on_because: str | None

    #: The absences consumed, verbatim. Never compensated for.
    absences: tuple[str, ...] = ()

    #: The decision this one supersedes — same subject, same question —
    #: or None where none preceded.
    predecessor: str | None = field(default=None)

    def __post_init__(self) -> None:
        if not self.decision_id.strip():
            raise ValueError("a decision carries its identity")
        if not self.occasion.strip():
            raise ValueError("a decision records the occasion that raised it")
        if not self.decided_by.strip():
            raise ValueError("a decision names its deterministic rule")

        if (self.verdict is None) == (self.refusal is None):
            raise ValueError("the outcome is exactly one of a verdict and a refusal")
        if (self.clauses is None) != (self.verdict is None):
            raise ValueError(
                "a verdict requires its clauses; a refusal requires only its reason"
            )
        if (self.facts is None) != (self.facts_because is not None):
            raise ValueError("established facts are present or absent with a reason")
        if (self.policy is None) != (self.policy_because is not None):
            raise ValueError("declared policy is present or absent with a reason")

        if (self.action is not None) and self.verdict is not DecisionVerdict.RECOMMEND:
            raise ValueError("an action attaches to RECOMMEND only")
        if self.verdict is DecisionVerdict.RECOMMEND and self.action is None:
            raise ValueError("RECOMMEND carries the question's affirmative action")

        if (self.raises is not None) != (self.verdict is DecisionVerdict.INVESTIGATE):
            raise ValueError("INVESTIGATE, and only INVESTIGATE, raises a question")
        if self.verdict is DecisionVerdict.INVESTIGATE:
            if self.question is DecisionQuestion.RESEARCH_SPEND:
                raise ValueError(
                    "INVESTIGATE is not a valid verdict for the research-spend "
                    "question: deferring whether to investigate into another "
                    "investigation decision would be circular"
                )
            if self.raises is not DecisionQuestion.RESEARCH_SPEND:
                raise ValueError("INVESTIGATE raises the research-spend question")

        if self.verdict is not None:
            if not self.weighed:
                raise ValueError("a verdict records the implications it weighed")
            if not any(implication.prevailed for implication in self.weighed):
                raise ValueError("a verdict names the implication that prevailed")
            if (self.rests_on is None) == (self.rests_on_because is None):
                raise ValueError(
                    "a verdict rests on the narrowest consumed agreement, or "
                    "carries the reason none was consumed"
                )

    @property
    def is_refusal(self) -> bool:
        """Whether the outcome is a refusal rather than a verdict."""

        return self.refusal is not None
