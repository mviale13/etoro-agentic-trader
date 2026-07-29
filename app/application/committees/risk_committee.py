"""Risk Committee."""

from __future__ import annotations

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
    Recommendation,
)
from app.brain import Brain


class RiskCommittee:
    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
    ) -> CommitteeOpinion:

        risk = reasoning.risk

        if risk.overall_risk_score >= 0.75:
            recommendation = Recommendation.SELL

        elif risk.overall_risk_score >= 0.50:
            recommendation = Recommendation.REDUCE

        else:
            recommendation = Recommendation.HOLD

        return CommitteeOpinion(
            committee="Risk Committee",
            recommendation=recommendation,
            confidence=1.0 - risk.overall_risk_score,
            summary="Portfolio risk evaluated.",
            evidence=risk.evidence,
        )
