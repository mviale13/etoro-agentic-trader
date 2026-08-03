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
            #
            # The confidence was 0.0, which read as a claim too — that this
            # committee was as good as certain of nothing. Averaged into
            # committee agreement it halved the figure, so an unmeasurable
            # portfolio risk looked like a committee voting against.
            return CommitteeOpinion(
                committee="Risk Committee",
                recommendation=Recommendation.HOLD,
                confidence=None,
                summary="Portfolio risk could not be measured.",
                evidence=risk.evidence,
            )

        if overall >= 0.75:
            recommendation = Recommendation.SELL

        elif overall >= 0.50:
            recommendation = Recommendation.REDUCE

        else:
            recommendation = Recommendation.HOLD

        # How well the risk was measured, not how low it came out. Under
        # `1.0 - overall` a clearly measured, severe risk reported low
        # confidence — the committee was surest of its SELL exactly when it
        # claimed to be least sure.
        return CommitteeOpinion(
            committee="Risk Committee",
            recommendation=recommendation,
            confidence=risk.confidence,
            summary="Portfolio risk evaluated.",
            evidence=risk.evidence,
        )
