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

        # The score decides what to recommend. It is not how sure the
        # committee is of it: reporting the score as confidence meant a
        # bearish view was, by construction, a tentative one, and a SELL
        # could never be stated with conviction. Confidence comes from how
        # well the assessments behind the view were evidenced.
        return CommitteeOpinion(
            committee="Investment Committee",
            recommendation=recommendation,
            confidence=(portfolio.confidence + market.confidence) / 2.0,
            summary=("Portfolio and market outlook evaluated."),
            evidence=evidence,
        )
