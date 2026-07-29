"""Investment Committee."""

from __future__ import annotations

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.brain import Brain


class InvestmentCommittee:
    """
    Reviews overall investment attractiveness.

    Focus:
    - Portfolio quality
    - Market quality
    """

    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
    ) -> CommitteeOpinion:

        portfolio = reasoning.portfolio
        market = reasoning.market

        score = portfolio.health_score * 0.60 + market.momentum_score * 0.40

        if score >= 0.85:
            recommendation = Recommendation.STRONG_BUY

        elif score >= 0.70:
            recommendation = Recommendation.BUY

        elif score >= 0.40:
            recommendation = Recommendation.HOLD

        elif score >= 0.20:
            recommendation = Recommendation.REDUCE

        else:
            recommendation = Recommendation.SELL

        evidence = (
            *portfolio.evidence,
            *market.evidence,
        )

        return CommitteeOpinion(
            committee="Investment Committee",
            recommendation=recommendation,
            confidence=score,
            summary=("Portfolio and market outlook evaluated."),
            evidence=evidence,
        )
