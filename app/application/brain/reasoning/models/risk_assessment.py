"""Risk reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.models.assessment import (
    AssessmentLevel,
    Evidence,
    assessment_level,
)


@dataclass(frozen=True, slots=True)
class RiskAssessment:
    """Structured interpretation of portfolio and market downside."""

    overall_risk_score: float
    market_risk_score: float
    concentration_risk_score: float
    liquidity_risk_score: float
    drawdown_risk_score: float
    confidence: float
    risk_factors: tuple[str, ...] = field(default_factory=tuple)
    mitigants: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "overall_risk_score",
            "market_risk_score",
            "concentration_risk_score",
            "liquidity_risk_score",
            "drawdown_risk_score",
            "confidence",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")

    @property
    def risk_level(self) -> AssessmentLevel:
        return assessment_level(self.overall_risk_score)
