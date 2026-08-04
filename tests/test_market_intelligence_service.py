"""The outlook, and what a crypto index is allowed to say about it."""

from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
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


def sentiment(score: int, label: str) -> SentimentSnapshot:
    return SentimentSnapshot(
        score=score,
        label=label,
        subject=AssetClass.CRYPTO,
        reading=Provenance(
            source="Alternative.me",
            observed_at=datetime.now(UTC),
        ),
    )


def test_the_outlook_follows_market_conditions() -> None:
    service = MarketIntelligenceService()

    assert service.build(build_market("positive"), None).outlook == "BULLISH"
    assert service.build(build_market("negative"), None).outlook == "BEARISH"
    assert service.build(build_market("neutral"), None).outlook == "NEUTRAL"


def test_crypto_fear_does_not_confirm_an_equity_sell_off() -> None:
    """
    It read BEARISH at 95%, summarised "weak market conditions are
    confirmed by crypto fear". Crypto fear is a different asset class
    having a different day, and corroboration it cannot give was raising
    the confidence of everything downstream.
    """

    alone = MarketIntelligenceService().build(build_market("negative"), None)

    with_fear = MarketIntelligenceService().build(
        build_market("negative", volatility="high"),
        sentiment(20, "Fear"),
    )

    assert with_fear.outlook == alone.outlook == "BEARISH"
    assert with_fear.confidence == alone.confidence

    assert "confirmed" not in with_fear.summary.lower()


def test_crypto_greed_does_not_lift_the_outlook_either() -> None:
    """The same misattribution, in the direction that flatters."""

    alone = MarketIntelligenceService().build(build_market("positive"), None)

    with_greed = MarketIntelligenceService().build(
        build_market("positive"),
        sentiment(72, "Greed"),
    )

    assert with_greed.outlook == alone.outlook == "BULLISH"
    assert with_greed.confidence == alone.confidence


def test_a_sentiment_reading_is_reported_with_the_class_it_describes() -> None:
    """Carried beside the outlook, never folded into it."""

    intelligence = MarketIntelligenceService().build(
        build_market("neutral"),
        sentiment(28, "Fear"),
    )

    assert intelligence.sentiment is not None
    assert "Crypto sentiment reads 28 (Fear)" in intelligence.summary
    assert "is not evidence about the rest of the market" in intelligence.summary


def test_the_confidence_says_how_narrow_the_reading_is() -> None:
    """
    One day's average move across nine instruments. A real reading and a
    narrow one, and it does not rise because an unrelated index agrees.
    """

    intelligence = MarketIntelligenceService().build(
        build_market("positive"),
        sentiment(72, "Greed"),
    )

    assert intelligence.confidence == MarketIntelligenceService.CONFIDENCE
    assert intelligence.confidence == 50
