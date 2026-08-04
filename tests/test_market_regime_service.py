from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_regime import MarketRegimeType
from app.domain.market_snapshot import MarketSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.services.market_regime_service import MarketRegimeService


def build_intelligence(
    outlook: str,
    confidence: int,
) -> MarketIntelligence:
    return MarketIntelligence(
        market=MarketSnapshot(
            quotes=(),
            market_mood="neutral",
            volatility="medium",
            summary="Test market.",
            timestamp=datetime.now(UTC),
        ),
        sentiment=SentimentSnapshot(
            score=50,
            label="Neutral",
            subject=AssetClass.CRYPTO,
            reading=Provenance(
                source="Test",
                observed_at=datetime.now(UTC),
            ),
        ),
        outlook=outlook,
        confidence=confidence,
        summary="Test intelligence.",
    )


def test_bullish_outlook_creates_bull_regime() -> None:
    regime = MarketRegimeService().detect(build_intelligence("BULLISH", 90))

    assert regime.regime == MarketRegimeType.BULL
    assert regime.confidence == 90


def test_bearish_outlook_creates_bear_regime() -> None:
    regime = MarketRegimeService().detect(build_intelligence("BEARISH", 95))

    assert regime.regime == MarketRegimeType.BEAR
    assert regime.confidence == 95


def test_neutral_outlook_creates_sideways_regime() -> None:
    regime = MarketRegimeService().detect(build_intelligence("NEUTRAL", 60))

    assert regime.regime == MarketRegimeType.SIDEWAYS
    assert regime.confidence == 60
