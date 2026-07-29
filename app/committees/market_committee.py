from app.domain.market_opinion import MarketOpinion
from app.domain.market_research import MarketResearch


class MarketCommittee:
    """Aggregate market specialist opinions."""

    def review(
        self,
        research: MarketResearch,
    ) -> MarketOpinion:
        score = round((research.equity_trend.score + research.market_breadth.score) / 2)

        confidence = round(
            (research.equity_trend.confidence + research.market_breadth.confidence) / 2,
            2,
        )

        rationale = (
            *research.equity_trend.evidence,
            *research.market_breadth.evidence,
        )

        return MarketOpinion(
            score=score,
            confidence=confidence,
            verdict="BULLISH",
            rationale=rationale,
        )
