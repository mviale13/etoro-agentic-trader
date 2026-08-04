from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
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
            subject=AssetClass.CRYPTO,
            reading=Provenance(
                source="Alternative.me",
                observed_at=datetime.now(UTC),
            ),
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
    # The crypto reading is named as crypto, and the equity absence is stated
    # beside it so it is not read as the mood of everything held.
    assert "Crypto sentiment" in output
    assert "No sentiment index is read for equities." in output


def test_the_equity_absence_is_stated_even_when_no_index_was_read(capsys):
    market = MarketSnapshot(
        quotes=(
            MarketQuote(symbol="SPY", name="S&P 500", price=600, change_percent=1),
        ),
        market_mood="positive",
        volatility="low",
        summary="Healthy market",
        timestamp=datetime.now(UTC),
    )

    intelligence = MarketIntelligence(
        market=market,
        sentiment=None,
        outlook="BULLISH",
        confidence=90,
        summary="Everything looks healthy.",
    )

    IntelligenceRenderer.render(intelligence)

    output = capsys.readouterr().out

    assert "not available" in output
    assert "No sentiment index is read for equities." in output
