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
    Reviews whether this security is an attractive investment.

    It used to review only the portfolio and the market, which are the same
    whichever security is being judged, so its opinion was identical under
    every symbol and told the Artificial CIO nothing about the case in
    front of it.

    The security's own committee view leads; the account and the market are
    the conditions it would be bought into. A security the Brain holds no
    evidence about produces no opinion at all — reviewing a case on context
    alone is precisely what this stopped doing.
    """

    #: What the security committee's own verdict is worth, as a ratio.
    SECURITY_VIEWS = {
        "BUY": 1.0,
        "HOLD": 0.5,
        "SELL": 0.0,
    }

    #: How far the security's own verdict outweighs its surroundings.
    SECURITY_WEIGHT = 0.60

    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
        symbol: str,
    ) -> CommitteeOpinion:

        portfolio = reasoning.portfolio
        market = reasoning.market

        company = brain.security_evidence(symbol)

        if company is None:
            return CommitteeOpinion(
                committee="Investment Committee",
                recommendation=Recommendation.HOLD,
                confidence=None,
                summary=(f"No security-level evidence is available for {symbol}."),
                evidence=(),
            )

        context = portfolio.health_score * 0.60 + market.momentum_score * 0.40

        security = self.SECURITY_VIEWS.get(company.recommendation, 0.5)

        score = security * self.SECURITY_WEIGHT + context * (1.0 - self.SECURITY_WEIGHT)

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
            confidence=(
                portfolio.confidence + market.confidence + company.confidence / 100.0
            )
            / 3.0,
            summary=(f"{symbol} evaluated against the portfolio and the market."),
            evidence=evidence,
        )
