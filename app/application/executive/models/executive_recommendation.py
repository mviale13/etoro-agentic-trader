"""Final recommendation produced by the Executive Committee."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.application.brain.reasoning.models.assessment import Evidence


class RecommendationAction(StrEnum):
    BUY = "buy"
    ADD = "add"
    HOLD = "hold"
    REDUCE = "reduce"
    SELL = "sell"
    WATCH = "watch"


@dataclass(frozen=True, slots=True)
class ExecutiveRecommendation:
    """Final explainable investment recommendation."""

    action: RecommendationAction

    confidence: float

    priority: float

    summary: str

    rationale: tuple[str, ...] = field(default_factory=tuple)

    risks: tuple[str, ...] = field(default_factory=tuple)

    opportunities: tuple[str, ...] = field(default_factory=tuple)

    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

        if not 0.0 <= self.priority <= 1.0:
            raise ValueError("priority must be between 0 and 1")
