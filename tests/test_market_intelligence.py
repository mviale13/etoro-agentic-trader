from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


def test_market_intelligence_is_immutable():
    intelligence = MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="positive",
            volatility="low",
            summary="Healthy market.",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=70,
            label="Greed",
            source="Alternative.me",
        ),
        outlook="BULLISH",
        confidence=90,
        summary="Markets remain constructive.",
    )

    assert intelligence.market.market_mood == "positive"
    assert intelligence.sentiment.score == 70
    assert intelligence.outlook == "BULLISH"
    assert intelligence.confidence == 90

    with pytest.raises(FrozenInstanceError):
        intelligence.outlook = "BEARISH"
