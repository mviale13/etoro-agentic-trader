from app.domain.equity_trend_opinion import (
    EquityTrendOpinion,
    EquityTrendVerdict,
)
from app.domain.market_breadth_opinion import (
    MarketBreadthOpinion,
    MarketBreadthVerdict,
)
from app.domain.market_research import MarketResearch


def test_market_research_contains_market_opinions() -> None:
    equity_trend = EquityTrendOpinion(
        score=85,
        confidence=1.0,
        verdict=EquityTrendVerdict.BULLISH,
        evidence=("SPY is trading above its long-term trend.",),
        uncertainty=(),
    )

    market_breadth = MarketBreadthOpinion(
        score=80,
        confidence=0.95,
        verdict=MarketBreadthVerdict.STRONG,
        evidence=("Most major indices are advancing together.",),
        uncertainty=(),
    )

    research = MarketResearch(
        equity_trend=equity_trend,
        market_breadth=market_breadth,
    )

    assert research.equity_trend is equity_trend
    assert research.market_breadth is market_breadth
