from app.committees.committee import Committee
from app.domain.company_research import CompanyResearch
from app.domain.fundamental_opinion import (
    FundamentalOpinion,
    FundamentalVerdict,
)


class FundamentalCommittee(Committee):
    """Aggregates specialist research into a fundamental opinion."""

    def review(
        self,
        research: CompanyResearch,
    ) -> FundamentalOpinion:
        opinions = (
            research.growth,
            research.profitability,
            research.balance_sheet,
            research.cash_flow,
        )

        score = self.aggregate_score(opinions)
        confidence = self.aggregate_confidence(opinions)

        return FundamentalOpinion(
            score=score,
            confidence=confidence,
            evidence=self.aggregate_evidence(opinions),
            uncertainty=self.aggregate_uncertainty(opinions),
            verdict=self._verdict_for(
                score=score,
                confidence=confidence,
            ),
        )

    @staticmethod
    def _verdict_for(
        *,
        score: int,
        confidence: float,
    ) -> FundamentalVerdict:
        if confidence == 0.0:
            return FundamentalVerdict.UNKNOWN

        if score >= 80:
            return FundamentalVerdict.STRONG_BUY

        if score >= 65:
            return FundamentalVerdict.BUY

        if score >= 45:
            return FundamentalVerdict.HOLD

        return FundamentalVerdict.SELL
