from datetime import datetime

from app.domain.equity_trend_opinion import EquityTrendVerdict
from app.domain.market_breadth_opinion import MarketBreadthVerdict
from app.domain.market_facts import MarketFact, MarketFacts
from app.services.market_research_service import MarketResearchService


def quote(
    symbol: str,
    change_percent: float,
) -> MarketFact:
    now = datetime.now()

    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change_percent,
        source="test",
        as_of=now,
    )


def test_market_research_service_runs_all_analysts() -> None:
    now = datetime.now()

    facts = MarketFacts(
        instruments=(
            quote("SPY", 1.2),
            quote("QQQ", 1.0),
            quote("IWM", 0.8),
            quote("DIA", 0.5),
        ),
        vix=None,
        source="test",
        as_of=now,
    )

    research = MarketResearchService().analyze(facts)

    trend = research.equity_trend

    assert trend.verdict is EquityTrendVerdict.BULLISH
    assert trend.confidence == 1.0
    assert len(trend.evidence) == 3
    assert trend.uncertainty == ()

    breadth = research.market_breadth

    assert breadth.verdict is MarketBreadthVerdict.STRONG
    assert breadth.confidence == 1.0
    assert len(breadth.evidence) == 4
    assert breadth.uncertainty == ()
