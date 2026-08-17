"""The executive conclusion over the wire, as an investor can argue with it.

Composed from `DecisionSynthesis` and from nothing else. No text is
written here, no fact is selected here and no absence is invented here:
this carries the domain's own strings, each with the origin the domain
attached to it.
"""

from pydantic import BaseModel

from app.domain.executive.decision_synthesis import (
    DecisionSynthesis,
    SynthesisFact,
)


class SynthesisFactResponse(BaseModel):
    """One fact in the conclusion, and how far it goes."""

    statement: str

    #: "established" — read from the company's own filing and checked
    #: against the cell it sits in. "assessed" — this platform's analysts
    #: reading market data. Shown, because side by side without it the
    #: weaker claim borrows the stronger's authority.
    origin: str

    #: Which committee stood on this fact. Null where no committee's
    #: remit covers it — never guessed at from the wording.
    committee: str | None = None


class ReviewConditionResponse(BaseModel):
    """A named condition for looking at this decision again."""

    condition: str
    origin: str

    #: What it would change, where the platform can say so. Null where
    #: the condition names a gap rather than an alternative conclusion.
    would_change: str | None


class UncertaintyResponse(BaseModel):
    """One thing a named committee could not settle."""

    committee: str
    kind: str
    about: str

    #: Whether another cycle of the same work could close it. False for
    #: a question no layer of this platform answers, so a surface never
    #: promises a measurement that is not coming.
    resolvable: bool


class DeliberationResponse(BaseModel):
    """Why this conclusion prevailed over the one that did not."""

    agreement: str
    prevailed: str

    #: The position that did not carry. Null where no committee
    #: contradicted the decision — preserved, never discarded.
    over: str | None

    because: str


class DecisionSynthesisResponse(BaseModel):
    """The decision stated as because / despite / review if.

    Every part may be empty, and an empty part carries the reason it is
    empty rather than a null a surface would have to explain. In
    particular a decision with no condition for review says so — the
    dossier does not borrow the account's conditions to fill the slot.
    """

    state: str

    #: Null where the CIO withheld one, carried through unchanged.
    conviction: int | None

    because: list[SynthesisFactResponse]
    because_absent: str | None

    despite: list[SynthesisFactResponse]
    despite_absent: str | None

    review_if: list[ReviewConditionResponse]
    review_if_absent: str | None

    #: What is not yet known. Its own part of the conclusion, never
    #: folded into the opposing case: a fact against the security is a
    #: reason to hesitate, and something unmeasured is a reason the
    #: platform cannot yet say.
    uncertainty: list[UncertaintyResponse]
    uncertainty_absent: str | None

    #: Why the positives currently outweigh the negatives, or the
    #: reverse. Null only where no committee took a position.
    deliberation: DeliberationResponse | None

    #: What the company's own filing establishes, carried beside the
    #: decision and marked as not having reached it.
    established: list[SynthesisFactResponse]

    #: Whether the investor is given anything to disagree with — an
    #: opposing fact or a condition for review. Reported rather than
    #: inferred on screen.
    challengeable: bool

    #: Whether the conclusion shows an argument rather than a checklist:
    #: something named as unresolved, or a position that did not carry.
    deliberated: bool


def synthesis_response(synthesis: DecisionSynthesis) -> DecisionSynthesisResponse:
    """The synthesis over the wire, carrying its strings unchanged."""

    return DecisionSynthesisResponse(
        state=synthesis.state.value,
        conviction=synthesis.conviction,
        because=[_fact(fact) for fact in synthesis.because],
        because_absent=synthesis.because_absent,
        despite=[_fact(fact) for fact in synthesis.despite],
        despite_absent=synthesis.despite_absent,
        review_if=[
            ReviewConditionResponse(
                condition=condition.condition,
                origin=condition.origin.value,
                would_change=condition.would_change,
            )
            for condition in synthesis.review_if
        ],
        review_if_absent=synthesis.review_if_absent,
        uncertainty=[
            UncertaintyResponse(
                committee=item.committee,
                kind=item.uncertainty.kind.value,
                about=item.about,
                resolvable=item.is_resolvable,
            )
            for item in synthesis.uncertainty
        ],
        uncertainty_absent=synthesis.uncertainty_absent,
        deliberation=(
            None
            if synthesis.deliberation is None
            else DeliberationResponse(
                agreement=synthesis.deliberation.agreement,
                prevailed=synthesis.deliberation.prevailed,
                over=synthesis.deliberation.over,
                because=synthesis.deliberation.because,
            )
        ),
        established=[_fact(fact) for fact in synthesis.established],
        challengeable=synthesis.is_challengeable,
        deliberated=synthesis.is_deliberated,
    )


def _fact(fact: SynthesisFact) -> SynthesisFactResponse:
    return SynthesisFactResponse(
        statement=fact.statement,
        origin=fact.origin.value,
        committee=fact.committee,
    )
