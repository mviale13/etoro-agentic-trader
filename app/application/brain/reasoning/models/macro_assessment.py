"""Macroeconomic reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.application.brain.reasoning.models.assessment import Evidence


class MacroRegime(StrEnum):
    """High-level economic regime."""

    EXPANSION = "expansion"
    SLOWDOWN = "slowdown"
    CONTRACTION = "contraction"
    RECOVERY = "recovery"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class MacroAssessment:
    """Structured interpretation of the macroeconomic environment."""

    regime: MacroRegime
    growth_score: float
    inflation_pressure_score: float
    monetary_tightness_score: float
    systemic_risk_score: float
    confidence: float
    tailwinds: tuple[str, ...] = field(default_factory=tuple)
    headwinds: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "growth_score",
            "inflation_pressure_score",
            "monetary_tightness_score",
            "systemic_risk_score",
            "confidence",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
