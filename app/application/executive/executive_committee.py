"""Executive Committee."""

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
from app.application.executive.decision_policy import DecisionPolicy
from app.application.executive.models.executive_recommendation import (
    ExecutiveRecommendation,
)


class ExecutiveCommittee:
    """Makes the final investment decision."""

    def __init__(self) -> None:
        self._policy = DecisionPolicy()

    def deliberate(
        self,
        portfolio: PortfolioAssessment,
        market: MarketAssessment,
        risk: RiskAssessment,
        behavior: BehaviorAssessment,
        opportunity: OpportunityAssessment,
    ) -> ExecutiveRecommendation:

        confidence = (
            portfolio.confidence
            + market.confidence
            + risk.confidence
            + behavior.confidence
            + opportunity.confidence
        ) / 5.0

        score = self._policy.score(
            portfolio=portfolio,
            market=market,
            risk=risk,
            behavior=behavior,
            opportunity=opportunity,
        )

        action = self._policy.recommendation(score)

        return ExecutiveRecommendation(
            action=action,
            confidence=confidence,
            priority=score,
            summary=f"Executive Committee recommends {action.value.upper()}.",
            rationale=("Decision synthesized from specialist assessments.",),
            opportunities=opportunity.opportunities,
            risks=opportunity.constraints,
            evidence=opportunity.evidence,
        )
