from app.application.brain.reasoning.models.assessment import Evidence
from app.application.brain.reasoning.models.behavior_assessment import (
    BehaviorAssessment,
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
from app.application.brain.reasoning.models.risk_assessment import (
    RiskAssessment,
)
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.executive.executive_committee import ExecutiveCommittee


def make_reasoning_snapshot(
    *,
    portfolio_confidence: float = 0.80,
    market_confidence: float = 0.70,
    risk_confidence: float = 0.90,
) -> ReasoningSnapshot:
    portfolio_evidence = Evidence(
        description="Portfolio liquidity remains strong.",
        source="portfolio",
        strength=0.90,
    )
    market_evidence = Evidence(
        description="Broad market momentum remains positive.",
        source="market",
        strength=0.75,
    )
    risk_evidence = Evidence(
        description="Current downside exposure is controlled.",
        source="risk",
        strength=0.80,
    )

    return ReasoningSnapshot(
        portfolio=PortfolioAssessment(
            health_score=0.80,
            diversification_score=0.70,
            concentration_risk=0.25,
            liquidity_score=0.85,
            confidence=portfolio_confidence,
            strengths=("Strong liquidity.",),
            weaknesses=("Some concentration remains.",),
            evidence=(portfolio_evidence,),
        ),
        market=MarketAssessment(
            trend=MarketTrend.BULLISH,
            regime=MarketRegime.RISK_ON,
            volatility_score=0.35,
            momentum_score=0.75,
            confidence=market_confidence,
            opportunities=("Positive market momentum.",),
            risks=("Volatility could increase.",),
            evidence=(market_evidence,),
        ),
        risk=RiskAssessment(
            overall_risk_score=0.25,
            market_risk_score=0.30,
            concentration_risk_score=0.25,
            liquidity_risk_score=0.10,
            drawdown_risk_score=0.30,
            confidence=risk_confidence,
            risk_factors=("Market reversal risk.",),
            mitigants=("High liquidity provides flexibility.",),
            evidence=(risk_evidence,),
        ),
        behavior=BehaviorAssessment(
            discipline_score=0.70,
            consistency_score=0.50,
            emotional_risk_score=0.30,
            policy_alignment_score=0.85,
            confidence=0.75,
            observed_biases=(),
            positive_behaviors=("Position sizing respects the policy.",),
            evidence=(),
        ),
        opportunity=OpportunityAssessment(
            opportunity_score=0.65,
            expected_upside_score=0.75,
            timing_score=0.70,
            portfolio_fit_score=0.72,
            confidence=0.75,
            opportunities=("Strong market momentum.",),
            constraints=(),
            evidence=(),
        ),
    )


def test_executive_committee_evaluates_reasoning_snapshot() -> None:
    recommendation = ExecutiveCommittee().evaluate(
        make_reasoning_snapshot(),
    )

    assert recommendation.action is not None
    assert recommendation.summary
    assert recommendation.rationale
    assert recommendation.opportunities == (
        "Strong liquidity.",
        "Positive market momentum.",
        "High liquidity provides flexibility.",
    )
    assert recommendation.risks == (
        "Some concentration remains.",
        "Volatility could increase.",
        "Market reversal risk.",
    )
    assert len(recommendation.evidence) == 3


def test_executive_committee_averages_specialist_confidence() -> None:
    recommendation = ExecutiveCommittee().evaluate(
        make_reasoning_snapshot(
            portfolio_confidence=0.60,
            market_confidence=0.75,
            risk_confidence=0.90,
        ),
    )

    assert recommendation.confidence == 0.75


def test_executive_committee_evaluation_is_deterministic() -> None:
    committee = ExecutiveCommittee()
    reasoning = make_reasoning_snapshot()

    first = committee.evaluate(reasoning)
    second = committee.evaluate(reasoning)

    assert first == second
