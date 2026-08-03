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
        overall = risk.overall_risk_score

        if overall is None:
            # Nothing measurable to hold an opinion about. Recommending HOLD
            # here would read as "risk is acceptable", which is a claim.
            return CommitteeOpinion(
                committee="Risk Committee",
                recommendation=Recommendation.HOLD,
                confidence=0.0,
                summary="Portfolio risk could not be measured.",
                evidence=risk.evidence,
            )

        if overall >= 0.75:
            recommendation = Recommendation.SELL

        elif overall >= 0.50:
            recommendation = Recommendation.REDUCE

        else:
            recommendation = Recommendation.HOLD

        return CommitteeOpinion(
            committee="Risk Committee",
            recommendation=recommendation,
            confidence=1.0 - overall,
            summary="Portfolio risk evaluated.",
            evidence=risk.evidence,
        )
