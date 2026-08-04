"""Investor behavior reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.models.assessment import Evidence


@dataclass(frozen=True, slots=True)
class BehaviorAssessment:
    """Structured interpretation of investor behavior and possible biases."""

    discipline_score: float
    consistency_score: float
    emotional_risk_score: float
    policy_alignment_score: float
    confidence: float
    observed_biases: tuple[str, ...] = field(default_factory=tuple)
    positive_behaviors: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "discipline_score",
            "consistency_score",
            "emotional_risk_score",
            "policy_alignment_score",
            "confidence",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
