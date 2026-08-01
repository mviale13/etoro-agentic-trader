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
from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.executive.decision_policy import DecisionPolicy
from app.application.executive.models.executive_recommendation import (
    ExecutiveRecommendation,
)


class ExecutiveCommittee:
    """
    Synthesizes specialist assessments into an executive recommendation.

    The canonical entry point is ``evaluate()``, which consumes the immutable
    output of the cognitive reasoning layer.

    ``deliberate()`` remains available for compatibility with the broader
    five-assessment committee flow.
    """

    def __init__(
        self,
        policy: DecisionPolicy | None = None,
    ) -> None:
        self._policy = policy or DecisionPolicy()

    def evaluate(
        self,
        reasoning: ReasoningSnapshot,
    ) -> ExecutiveRecommendation:
        """
        Evaluate the collective portfolio, market and risk reasoning.

        The committee receives interpreted assessments only. It has no
        dependency on Brain, brokers, APIs, portfolio services or the UI.
        """

        portfolio = reasoning.portfolio
        market = reasoning.market
        risk = reasoning.risk

        confidence = (portfolio.confidence + market.confidence + risk.confidence) / 3.0

        score = (
            portfolio.health_score * 0.35
            + market.momentum_score * 0.25
            + (1.0 - risk.overall_risk_score) * 0.40
        )

        action = self._policy.recommendation(score)

        opportunities = tuple(
            dict.fromkeys(
                (
                    *portfolio.strengths,
                    *market.opportunities,
                    *risk.mitigants,
                )
            )
        )

        risks = tuple(
            dict.fromkeys(
                (
                    *portfolio.weaknesses,
                    *market.risks,
                    *risk.risk_factors,
                )
            )
        )

        evidence = tuple(
            dict.fromkeys(
                (
                    *portfolio.evidence,
                    *market.evidence,
                    *risk.evidence,
                )
            )
        )

        rationale = self._build_rationale(
            portfolio=portfolio,
            market=market,
            risk=risk,
        )

        return ExecutiveRecommendation(
            action=action,
            confidence=confidence,
            priority=score,
            summary=(
                "Executive Committee synthesized the portfolio, "
                f"market and risk assessments into {action.value.upper()}."
            ),
            rationale=rationale,
            opportunities=opportunities,
            risks=risks,
            evidence=evidence,
        )

    def deliberate(
        self,
        portfolio: PortfolioAssessment,
        market: MarketAssessment,
        risk: RiskAssessment,
        behavior: BehaviorAssessment,
        opportunity: OpportunityAssessment,
    ) -> ExecutiveRecommendation:
        """
        Preserve the existing five-assessment committee interface.

        This flow remains available until behavior and opportunity assessments
        become part of the canonical ReasoningSnapshot.
        """

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

    @staticmethod
    def _build_rationale(
        portfolio: PortfolioAssessment,
        market: MarketAssessment,
        risk: RiskAssessment,
    ) -> tuple[str, ...]:
        rationale = [
            (f"Portfolio health is {portfolio.health_level.value.replace('_', ' ')}."),
            (
                "Market conditions are "
                f"{market.regime.value.replace('_', ' ')} with "
                f"{market.trend.value.replace('_', ' ')} momentum."
            ),
            (f"Overall risk is {risk.risk_level.value.replace('_', ' ')}."),
        ]

        return tuple(rationale)
