"""Committee opinion model."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.application.brain.reasoning.models.assessment import Evidence


class Recommendation(StrEnum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    REDUCE = "reduce"
    SELL = "sell"


@dataclass(frozen=True, slots=True)
class CommitteeOpinion:
    """
    Opinion produced by an Executive Committee.

    Committees never execute trades.
    They advise the Artificial CIO.
    """

    committee: str

    recommendation: Recommendation

    #: How sure this committee is of its own view, given how well the
    #: assessments behind it were evidenced.
    #:
    #: None when the committee could not form a view at all. That is not
    #: the same as being unconvinced, and averaging it in as a zero said
    #: the opposite: a portfolio whose risk could not be measured dragged
    #: committee agreement down as though a committee had objected.
    confidence: float | None

    summary: str

    evidence: tuple[Evidence, ...]

    @property
    def has_opinion(self) -> bool:
        return self.confidence is not None
