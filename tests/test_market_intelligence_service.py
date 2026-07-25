from datetime import UTC, datetime

from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
)


def build_market(
    mood: str,
    *,
    volatility: str = "low",
) -> MarketSnapshot:
    return MarketSnapshot(
        quotes=(
            MarketQuote(
                symbol="SPY",
                name="S&P 500",
                price=600,
                change_percent=1,
            ),
        ),
        market_mood=mood,
        volatility=volatility,
        summary="Test market snapshot.",
        timestamp=datetime.now(UTC),
    )


def test_positive_market_and_greed_are_bullish():
    intelligence = MarketIntelligenceService().build(
        market=build_market("positive"),
        sentiment=SentimentSnapshot(
            score=72,
            label="Greed",
            source="Alternative.me",
        ),
    )

    assert intelligence.outlook == "BULLISH"
    assert intelligence.confidence == 90
    assert "aligned" in intelligence.summary.lower()


def test_negative_market_and_fear_are_bearish():
    intelligence = MarketIntelligenceService().build(
        market=build_market(
            "negative",
            volatility="high",
        ),
        sentiment=SentimentSnapshot(
            score=20,
            label="Fear",
            source="Alternative.me",
        ),
    )

    assert intelligence.outlook == "BEARISH"
    assert intelligence.confidence == 95
    assert "confirmed" in intelligence.summary.lower()


def test_mixed_conditions_are_neutral():
    intelligence = MarketIntelligenceService().build(
        market=build_market("positive"),
        sentiment=SentimentSnapshot(
            score=35,
            label="Fear",
            source="Alternative.me",
        ),
    )

    assert intelligence.outlook == "NEUTRAL"
    assert intelligence.confidence == 60
    assert "mixed" in intelligence.summary.lower()


def test_neutral_market_is_neutral():
    intelligence = MarketIntelligenceService().build(
        market=build_market(
            "neutral",
            volatility="medium",
        ),
        sentiment=SentimentSnapshot(
            score=50,
            label="Neutral",
            source="Alternative.me",
        ),
    )

    assert intelligence.outlook == "NEUTRAL"
    assert intelligence.confidence == 60
