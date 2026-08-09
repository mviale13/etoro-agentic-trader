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


class ReviewConditionResponse(BaseModel):
    """A named condition for looking at this decision again."""

    condition: str
    origin: str

    #: What it would change, where the platform can say so. Null where
    #: the condition names a gap rather than an alternative conclusion.
    would_change: str | None


class DecisionSynthesisResponse(BaseModel):
    """The decision stated as because / despite / review if.

    Every part may be empty, and an empty part carries the reason it is
    empty rather than a null a surface would have to explain. In
    particular a decision with no condition for review says so — the
    dossier does not borrow the account's conditions to fill the slot.
    """

    state: str
    conviction: int

    because: list[SynthesisFactResponse]
    because_absent: str | None

    despite: list[SynthesisFactResponse]
    despite_absent: str | None

    review_if: list[ReviewConditionResponse]
    review_if_absent: str | None

    #: What the company's own filing establishes, carried beside the
    #: decision and marked as not having reached it.
    established: list[SynthesisFactResponse]

    #: Whether the investor is given anything to disagree with — an
    #: opposing fact or a condition for review. Reported rather than
    #: inferred on screen.
    challengeable: bool


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
        established=[_fact(fact) for fact in synthesis.established],
        challengeable=synthesis.is_challengeable,
    )


def _fact(fact: SynthesisFact) -> SynthesisFactResponse:
    return SynthesisFactResponse(statement=fact.statement, origin=fact.origin.value)
