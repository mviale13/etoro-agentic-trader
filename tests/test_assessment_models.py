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
        portfolio_readiness_score=0.9,
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
