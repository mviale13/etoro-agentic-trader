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

    confidence: float

    summary: str

    evidence: tuple[Evidence, ...]
