"""Market reasoning output."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.application.brain.reasoning.models.assessment import Evidence


class MarketTrend(StrEnum):
    """High-level direction of the observed market."""

    STRONGLY_BEARISH = "strongly_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    STRONGLY_BULLISH = "strongly_bullish"


class MarketRegime(StrEnum):
    """High-level market regime."""

    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    TRANSITION = "transition"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class MarketAssessment:
    """Structured interpretation of current market conditions."""

    trend: MarketTrend
    regime: MarketRegime
    volatility_score: float
    momentum_score: float
    confidence: float
    opportunities: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for field_name in (
            "volatility_score",
            "momentum_score",
            "confidence",
        ):
            value = getattr(self, field_name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{field_name} must be between 0.0 and 1.0")
