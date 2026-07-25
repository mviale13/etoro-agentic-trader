from datetime import UTC, datetime

from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.renderers.intelligence_renderer import IntelligenceRenderer


def test_renderer_outputs_information(capsys):
    market = MarketSnapshot(
        quotes=(
            MarketQuote(
                symbol="SPY",
                name="S&P 500",
                price=600,
                change_percent=1,
            ),
        ),
        market_mood="positive",
        volatility="low",
        summary="Healthy market",
        timestamp=datetime.now(UTC),
    )

    intelligence = MarketIntelligence(
        market=market,
        sentiment=SentimentSnapshot(
            score=72,
            label="Greed",
            source="Alternative.me",
        ),
        outlook="BULLISH",
        confidence=90,
        summary="Everything looks healthy.",
    )

    IntelligenceRenderer.render(intelligence)

    output = capsys.readouterr().out

    assert "MARKET INTELLIGENCE" in output
    assert "BULLISH" in output
    assert "90%" in output
    assert "Greed" in output
