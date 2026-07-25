from datetime import UTC, datetime

from app.committee.momentum import MomentumCommittee
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


def intelligence(outlook: str) -> MarketIntelligence:
    return MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="positive",
            volatility="low",
            summary="Healthy",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=70,
            label="Greed",
            source="Alternative.me",
        ),
        outlook=outlook,
        confidence=80,
        summary="Healthy market.",
    )


def test_buy_vote():
    opinion = MomentumCommittee().evaluate(intelligence("BULLISH"))

    assert opinion.vote == "BUY"


def test_sell_vote():
    opinion = MomentumCommittee().evaluate(intelligence("BEARISH"))

    assert opinion.vote == "SELL"


def test_hold_vote():
    opinion = MomentumCommittee().evaluate(intelligence("NEUTRAL"))

    assert opinion.vote == "HOLD"
