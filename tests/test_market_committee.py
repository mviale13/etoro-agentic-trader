from app.committees.market_committee import MarketCommittee
from app.domain.equity_trend_opinion import (
    EquityTrendOpinion,
    EquityTrendVerdict,
)
from app.domain.market_breadth_opinion import (
    MarketBreadthOpinion,
    MarketBreadthVerdict,
)
from app.domain.market_research import MarketResearch


def test_market_committee_builds_market_opinion() -> None:
    research = MarketResearch(
        equity_trend=EquityTrendOpinion(
            score=90,
            confidence=0.9,
            evidence=("Trend is positive.",),
            uncertainty=(),
            verdict=EquityTrendVerdict.BULLISH,
        ),
        market_breadth=MarketBreadthOpinion(
            score=95,
            confidence=0.8,
            evidence=("Breadth is strong.",),
            uncertainty=(),
            verdict=MarketBreadthVerdict.STRONG,
        ),
    )

    opinion = MarketCommittee().review(research)

    assert opinion.score == 92
    assert opinion.confidence == 0.85
    assert opinion.verdict == "BULLISH"
