"""Opportunity reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brain.reasoning.models.assessment import (
    AssessmentLevel,
    Evidence,
    assessment_level,
)


@dataclass(frozen=True, slots=True)
class OpportunityAssessment:
    """Structured interpretation of potential investment upside."""

    opportunity_score: float
    expected_upside_score: float
    timing_score: float
    portfolio_fit_score: float
    confidence: float
    opportunities: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "opportunity_score",
            "expected_upside_score",
            "timing_score",
            "portfolio_fit_score",
            "confidence",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")

    @property
    def opportunity_level(self) -> AssessmentLevel:
        return assessment_level(self.opportunity_score)
