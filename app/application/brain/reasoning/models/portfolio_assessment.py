"""Portfolio reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.models.assessment import (
    AssessmentLevel,
    Evidence,
    assessment_level,
)


@dataclass(frozen=True, slots=True)
class PortfolioAssessment:
    """Structured interpretation of portfolio quality and resilience."""

    health_score: float
    diversification_score: float
    concentration_risk: float
    liquidity_score: float
    confidence: float
    strengths: tuple[str, ...] = field(default_factory=tuple)
    weaknesses: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "health_score",
            "diversification_score",
            "concentration_risk",
            "liquidity_score",
            "confidence",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")

    @property
    def health_level(self) -> AssessmentLevel:
        return assessment_level(self.health_score)
