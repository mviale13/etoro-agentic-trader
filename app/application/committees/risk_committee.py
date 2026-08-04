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
    """
    Reviews the risk of holding this security.

    It used to review only the account's risk, which needs position history
    nothing records, so it abstained on every symbol — including securities
    whose own volatility and deepest fall had been measured from a year of
    prices. Where the security's risk is known it is what this committee
    speaks to; the account's risk is the fallback, and silence is what
    remains when neither was measured.
    """

    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
        symbol: str,
    ) -> CommitteeOpinion:

        company = brain.security_evidence(symbol)

        if company is not None and company.signals.risk is not None:
            security_risk = company.signals.risk

            if security_risk.severity is not None:
                return CommitteeOpinion(
                    committee="Risk Committee",
                    recommendation=self._recommendation(security_risk.severity),
                    confidence=security_risk.confidence / 100.0,
                    summary=(
                        f"{symbol} carries {security_risk.level.lower()} risk on "
                        "its own price history."
                    ),
                    evidence=(),
                )

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

        recommendation = self._recommendation(overall)

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

    @staticmethod
    def _recommendation(severity: float) -> Recommendation:
        """The same bands whether the risk is the security's or the account's."""

        if severity >= 0.75:
            return Recommendation.SELL

        if severity >= 0.50:
            return Recommendation.REDUCE

        return Recommendation.HOLD
