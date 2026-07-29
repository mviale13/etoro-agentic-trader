"""Investment decision policy."""

from __future__ import annotations

from app.application.brain.reasoning.models.behavior_assessment import (
    BehaviorAssessment,
)
from app.application.brain.reasoning.models.market_assessment import (
    MarketAssessment,
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
from app.application.executive.models.executive_recommendation import (
    RecommendationAction,
)


class DecisionPolicy:
    """Transforms specialist assessments into an executive decision."""

    def score(
        self,
        portfolio: PortfolioAssessment,
        market: MarketAssessment,
        risk: RiskAssessment,
        behavior: BehaviorAssessment,
        opportunity: OpportunityAssessment,
    ) -> float:
        """Compute the committee score."""

        market_strength = (
            market.momentum_score + (1.0 - market.volatility_score)
        ) / 2.0

        return (
            opportunity.opportunity_score * 0.40
            + market_strength * 0.20
            + portfolio.health_score * 0.20
            + behavior.discipline_score * 0.10
            + (1.0 - risk.overall_risk_score) * 0.10
        )

    def recommendation(
        self,
        score: float,
    ) -> RecommendationAction:
        """Convert a score into an investment recommendation."""

        if score >= 0.90:
            return RecommendationAction.BUY

        if score >= 0.75:
            return RecommendationAction.ADD

        if score >= 0.55:
            return RecommendationAction.HOLD

        if score >= 0.35:
            return RecommendationAction.REDUCE

        return RecommendationAction.SELL
