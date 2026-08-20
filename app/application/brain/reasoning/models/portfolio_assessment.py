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

    #: None where liquidity could not be measured, because liquidity is
    #: a quarter of this score. Health computed as though unreadable cash
    #: were no cash is a fabricated number wearing a measured name — the
    #: same rule `RiskAnalyst._overall` already applies to its own four
    #: components.
    health_score: float | None

    diversification_score: float
    concentration_risk: float

    #: None where the broker stated no cash figure. Not 0.0: that would
    #: report the least liquid possible account for one nobody measured.
    liquidity_score: float | None

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

            if value is None:
                continue

            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")

    @property
    def health_level(self) -> AssessmentLevel | None:
        """The band, or nothing while the score itself is unmeasured."""

        if self.health_score is None:
            return None

        return assessment_level(self.health_score)
