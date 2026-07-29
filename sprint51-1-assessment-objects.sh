#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="app/application/brain/reasoning"
MODELS_DIR="${BASE_DIR}/models"

mkdir -p "${MODELS_DIR}"

cat > "${BASE_DIR}/__init__.py" <<'PY'
"""Reasoning layer for the MOVRvest Investment Brain."""
PY

cat > "${MODELS_DIR}/assessment.py" <<'PY'
"""Shared primitives used by reasoning assessments."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class AssessmentLevel(StrEnum):
    """Normalized qualitative interpretation of an assessment score."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True, slots=True)
class Evidence:
    """A traceable fact supporting or opposing an assessment."""

    description: str
    source: str
    strength: float

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError("Evidence description cannot be empty")

        if not self.source.strip():
            raise ValueError("Evidence source cannot be empty")

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("Evidence strength must be between 0.0 and 1.0")


def assessment_level(score: float) -> AssessmentLevel:
    """Convert a normalized score into a qualitative assessment level."""

    if not 0.0 <= score <= 1.0:
        raise ValueError("Assessment score must be between 0.0 and 1.0")

    if score < 0.2:
        return AssessmentLevel.VERY_LOW
    if score < 0.4:
        return AssessmentLevel.LOW
    if score < 0.6:
        return AssessmentLevel.MODERATE
    if score < 0.8:
        return AssessmentLevel.HIGH

    return AssessmentLevel.VERY_HIGH
PY

cat > "${MODELS_DIR}/portfolio_assessment.py" <<'PY'
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
PY

cat > "${MODELS_DIR}/market_assessment.py" <<'PY'
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
PY

cat > "${MODELS_DIR}/risk_assessment.py" <<'PY'
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
PY

cat > "${MODELS_DIR}/opportunity_assessment.py" <<'PY'
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
PY

cat > "${MODELS_DIR}/behavior_assessment.py" <<'PY'
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
PY

cat > "${MODELS_DIR}/macro_assessment.py" <<'PY'
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
PY

cat > "${MODELS_DIR}/__init__.py" <<'PY'
"""Assessment models produced by the MOVRvest reasoning layer."""

from app.application.brain.reasoning.models.assessment import (
    AssessmentLevel,
    Evidence,
    assessment_level,
)
from app.application.brain.reasoning.models.behavior_assessment import (
    BehaviorAssessment,
)
from app.application.brain.reasoning.models.macro_assessment import (
    MacroAssessment,
    MacroRegime,
)
from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
    MarketRegime,
    MarketTrend,
)
from app.application.brain.reasoning.models.opportunity_assessment import (
    OpportunityAssessment,
)
from app.application.brain.reasoning.models.portfolio_assessment import (
    PortfolioAssessment,
)
from app.application.brain.reasoning.models.risk_assessment import RiskAssessment

__all__ = [
    "AssessmentLevel",
    "BehaviorAssessment",
    "Evidence",
    "MacroAssessment",
    "MacroRegime",
    "MarketAssessment",
    "MarketRegime",
    "MarketTrend",
    "OpportunityAssessment",
    "PortfolioAssessment",
    "RiskAssessment",
    "assessment_level",
]
PY

cat > tests/test_assessment_models.py <<'PY'
import pytest

from app.application.brain.reasoning.models import (
    AssessmentLevel,
    BehaviorAssessment,
    Evidence,
    MacroAssessment,
    MacroRegime,
    MarketAssessment,
    MarketRegime,
    MarketTrend,
    OpportunityAssessment,
    PortfolioAssessment,
    RiskAssessment,
    assessment_level,
)


def test_assessment_level_maps_normalized_scores() -> None:
    assert assessment_level(0.10) is AssessmentLevel.VERY_LOW
    assert assessment_level(0.30) is AssessmentLevel.LOW
    assert assessment_level(0.50) is AssessmentLevel.MODERATE
    assert assessment_level(0.70) is AssessmentLevel.HIGH
    assert assessment_level(0.90) is AssessmentLevel.VERY_HIGH


def test_assessment_level_rejects_invalid_score() -> None:
    with pytest.raises(ValueError):
        assessment_level(1.01)


def test_evidence_is_traceable_and_validated() -> None:
    evidence = Evidence(
        description="Technology exposure exceeds policy target",
        source="portfolio_snapshot",
        strength=0.9,
    )

    assert evidence.source == "portfolio_snapshot"
    assert evidence.strength == 0.9


def test_evidence_rejects_invalid_strength() -> None:
    with pytest.raises(ValueError):
        Evidence(
            description="Invalid evidence",
            source="test",
            strength=-0.1,
        )


def test_portfolio_assessment_exposes_health_level() -> None:
    assessment = PortfolioAssessment(
        health_score=0.72,
        diversification_score=0.64,
        concentration_risk=0.42,
        liquidity_score=0.85,
        confidence=0.9,
        strengths=("Strong liquidity",),
        weaknesses=("Technology concentration",),
    )

    assert assessment.health_level is AssessmentLevel.HIGH
    assert assessment.strengths == ("Strong liquidity",)


def test_market_assessment_describes_conditions_without_deciding() -> None:
    assessment = MarketAssessment(
        trend=MarketTrend.BULLISH,
        regime=MarketRegime.RISK_ON,
        volatility_score=0.35,
        momentum_score=0.74,
        confidence=0.81,
        opportunities=("Positive equity momentum",),
        risks=("Valuations are elevated",),
    )

    assert assessment.trend is MarketTrend.BULLISH
    assert not hasattr(assessment, "recommendation")
    assert not hasattr(assessment, "action")


def test_risk_assessment_exposes_risk_level() -> None:
    assessment = RiskAssessment(
        overall_risk_score=0.65,
        market_risk_score=0.7,
        concentration_risk_score=0.6,
        liquidity_risk_score=0.2,
        drawdown_risk_score=0.55,
        confidence=0.8,
    )

    assert assessment.risk_level is AssessmentLevel.HIGH


def test_opportunity_assessment_exposes_opportunity_level() -> None:
    assessment = OpportunityAssessment(
        opportunity_score=0.82,
        expected_upside_score=0.78,
        timing_score=0.7,
        portfolio_fit_score=0.9,
        confidence=0.76,
    )

    assert assessment.opportunity_level is AssessmentLevel.VERY_HIGH


def test_behavior_assessment_contains_behavioral_signals() -> None:
    assessment = BehaviorAssessment(
        discipline_score=0.8,
        consistency_score=0.7,
        emotional_risk_score=0.25,
        policy_alignment_score=0.9,
        confidence=0.65,
        observed_biases=("Recency bias",),
    )

    assert assessment.observed_biases == ("Recency bias",)


def test_macro_assessment_contains_macro_regime() -> None:
    assessment = MacroAssessment(
        regime=MacroRegime.SLOWDOWN,
        growth_score=0.35,
        inflation_pressure_score=0.58,
        monetary_tightness_score=0.72,
        systemic_risk_score=0.4,
        confidence=0.7,
    )

    assert assessment.regime is MacroRegime.SLOWDOWN


@pytest.mark.parametrize(
    "assessment",
    [
        PortfolioAssessment(
            health_score=1.1,
            diversification_score=0.5,
            concentration_risk=0.5,
            liquidity_score=0.5,
            confidence=0.5,
        ),
        MarketAssessment(
            trend=MarketTrend.NEUTRAL,
            regime=MarketRegime.UNCERTAIN,
            volatility_score=-0.1,
            momentum_score=0.5,
            confidence=0.5,
        ),
    ],
)
def test_assessments_reject_scores_outside_normalized_range(
    assessment: object,
) -> None:
    # Construction happens during parametrization, so this body is unreachable.
    # The cases are retained below as explicit validation tests instead.
    assert assessment is not None


def test_portfolio_assessment_rejects_invalid_score() -> None:
    with pytest.raises(ValueError):
        PortfolioAssessment(
            health_score=1.1,
            diversification_score=0.5,
            concentration_risk=0.5,
            liquidity_score=0.5,
            confidence=0.5,
        )


def test_market_assessment_rejects_invalid_score() -> None:
    with pytest.raises(ValueError):
        MarketAssessment(
            trend=MarketTrend.NEUTRAL,
            regime=MarketRegime.UNCERTAIN,
            volatility_score=-0.1,
            momentum_score=0.5,
            confidence=0.5,
        )
PY

# Remove the intentionally invalid parametrized block before running tests.
python - <<'PY'
from pathlib import Path

path = Path("tests/test_assessment_models.py")
content = path.read_text()

start = content.index('\n\n@pytest.mark.parametrize(\n')
end = content.index('\n\ndef test_portfolio_assessment_rejects_invalid_score()', start)

path.write_text(content[:start] + content[end:])
PY

echo
echo "Assessment objects created."
echo
echo "Run:"
echo "  ruff check --fix app/application/brain/reasoning tests/test_assessment_models.py"
echo "  ruff format app/application/brain/reasoning tests/test_assessment_models.py"
echo "  mypy app/application/brain/reasoning tests/test_assessment_models.py"
echo "  pytest tests/test_assessment_models.py"
