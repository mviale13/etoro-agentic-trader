"""Opportunity reasoning engine."""

from __future__ import annotations

from app.application.brain.reasoning.models.assessment import Evidence
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


class OpportunityReasoner:
    """Synthesizes specialist assessments into an investment opportunity."""

    def assess(
        self,
        portfolio: PortfolioAssessment,
        market: MarketAssessment,
        risk: RiskAssessment,
        behavior: BehaviorAssessment,
    ) -> OpportunityAssessment:
        expected_upside = market.momentum_score

        timing = (market.momentum_score + (1.0 - market.volatility_score)) / 2.0

        portfolio_fit = (
            portfolio.diversification_score
            + behavior.policy_alignment_score
            + (1.0 - risk.overall_risk_score)
        ) / 3.0

        opportunity = expected_upside * 0.40 + timing * 0.30 + portfolio_fit * 0.30

        opportunity *= 1.0 - risk.overall_risk_score * 0.25

        opportunity = max(0.0, min(opportunity, 1.0))

        confidence = (
            portfolio.confidence
            + market.confidence
            + risk.confidence
            + behavior.confidence
        ) / 4.0

        opportunities: list[str] = []
        constraints: list[str] = []
        evidence: list[Evidence] = []

        if market.momentum_score > 0.70:
            opportunities.append("Strong market momentum")

        if portfolio.diversification_score > 0.80:
            opportunities.append("Well diversified portfolio")

        if behavior.policy_alignment_score > 0.80:
            opportunities.append("Portfolio aligns with investment policy")

        if risk.overall_risk_score > 0.60:
            constraints.append("Elevated portfolio risk")

        if market.volatility_score > 0.70:
            constraints.append("High market volatility")

        evidence.append(
            Evidence(
                description=(f"Market momentum score is {market.momentum_score:.2f}."),
                source="MarketAssessment",
                strength=market.confidence,
            )
        )

        evidence.append(
            Evidence(
                description=(
                    f"Overall portfolio risk score is {risk.overall_risk_score:.2f}."
                ),
                source="RiskAssessment",
                strength=risk.confidence,
            )
        )

        evidence.append(
            Evidence(
                description=(f"Portfolio fit score is {portfolio_fit:.2f}."),
                source="PortfolioAssessment",
                strength=portfolio.confidence,
            )
        )

        return OpportunityAssessment(
            opportunity_score=opportunity,
            expected_upside_score=expected_upside,
            timing_score=timing,
            portfolio_fit_score=portfolio_fit,
            confidence=confidence,
            opportunities=tuple(opportunities),
            constraints=tuple(constraints),
            evidence=tuple(evidence),
        )
