from datetime import UTC, datetime

from app.domain.market_facts import (
    MarketFact,
    MarketFacts,
)
from app.services.market_breadth_service import (
    MarketBreadthService,
)

NOW = datetime.now(
    UTC,
)


def fact(
    symbol: str,
    change_percent: float,
) -> MarketFact:
    return MarketFact(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change_percent,
        source="test",
        as_of=NOW,
    )


def test_builds_positive_market_breadth() -> None:
    facts = MarketFacts(
        instruments=(
            fact("SPY", 0.8),
            fact("QQQ", 1.2),
            fact("IWM", 0.5),
            fact("BTC", 2.0),
            fact("ETH", 1.5),
            fact("GLD", -0.2),
            fact("WTI", 0.4),
            fact("DXY", 0.1),
            fact("TNX", 0.3),
        ),
        vix=14.0,
        source="test",
        as_of=NOW,
    )

    breadth = MarketBreadthService().build(
        facts,
    )

    assert breadth.equities == "positive"
    assert breadth.technology == "positive"
    assert breadth.small_caps == "positive"
    assert breadth.crypto == "positive"
    assert breadth.commodities == "neutral"
    assert breadth.volatility == "low"
    assert breadth.dollar == "neutral"
    assert breadth.rates == "positive"


def test_builds_defensive_market_breadth() -> None:
    facts = MarketFacts(
        instruments=(
            fact("SPY", -1.0),
            fact("QQQ", -1.6),
            fact("IWM", -1.2),
            fact("BTC", -3.0),
            fact("ETH", -4.0),
            fact("GLD", 1.0),
            fact("WTI", -0.8),
            fact("DXY", 0.7),
            fact("TNX", -0.4),
        ),
        vix=31.0,
        source="test",
        as_of=NOW,
    )

    breadth = MarketBreadthService().build(
        facts,
    )

    assert breadth.equities == "negative"
    assert breadth.technology == "negative"
    assert breadth.crypto == "negative"
    assert breadth.volatility == "high"
    assert breadth.dollar == "positive"
    assert breadth.rates == "negative"


def test_handles_missing_market_facts() -> None:
    facts = MarketFacts(
        instruments=(),
        vix=None,
        source="test",
        as_of=NOW,
    )

    breadth = MarketBreadthService().build(
        facts,
    )

    assert breadth.equities == "unknown"
    assert breadth.crypto == "unknown"
    assert breadth.volatility == "unknown"
