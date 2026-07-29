from app.domain.company_research import CompanyResearch
from app.domain.fundamental_opinion import (
    FundamentalOpinion,
    FundamentalVerdict,
)


class FundamentalCommittee:
    def evaluate(
        self,
        research: CompanyResearch,
    ) -> FundamentalOpinion:
        opinions = (
            research.growth,
            research.profitability,
            research.balance_sheet,
            research.cash_flow,
        )

        scores = tuple(
            opinion.score for opinion in opinions if opinion.score is not None
        )

        if not scores:
            return FundamentalOpinion(
                score=None,
                confidence=0.0,
                verdict=FundamentalVerdict.UNKNOWN,
                evidence=(),
                uncertainty=("No analyst opinions available.",),
            )

        score = round(sum(scores) / len(scores))

        confidence = sum(opinion.confidence for opinion in opinions) / len(opinions)

        evidence = tuple(item for opinion in opinions for item in opinion.evidence)

        uncertainty = tuple(
            item for opinion in opinions for item in opinion.uncertainty
        )

        return FundamentalOpinion(
            score=score,
            confidence=confidence,
            verdict=self._verdict(score),
            evidence=evidence,
            uncertainty=uncertainty,
        )

    @staticmethod
    def _verdict(
        score: int,
    ) -> FundamentalVerdict:
        if score >= 90:
            return FundamentalVerdict.STRONG_BUY

        if score >= 75:
            return FundamentalVerdict.BUY

        if score >= 50:
            return FundamentalVerdict.HOLD

        return FundamentalVerdict.SELL
