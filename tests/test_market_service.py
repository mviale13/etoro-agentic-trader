from datetime import datetime, timezone

from app.domain.market_snapshot import MarketQuote
from app.services.market_service import MarketService


def test_positive_low_volatility_market():
    quotes = (
        MarketQuote(
            symbol="SPY",
            name="S&P 500 ETF",
            price=600,
            change_percent=0.8,
        ),
        MarketQuote(
            symbol="BTC",
            name="Bitcoin",
            price=100_000,
            change_percent=1.2,
        ),
    )

    snapshot = MarketService().build_snapshot(
        quotes,
        vix=12,
        timestamp=datetime.now(timezone.utc),
    )

    assert snapshot.market_mood == "positive"
    assert snapshot.volatility == "low"
    assert snapshot.summary == "Markets are positive and volatility is low."


def test_negative_high_volatility_market():
    quotes = (
        MarketQuote(
            symbol="SPY",
            name="S&P 500 ETF",
            price=600,
            change_percent=-1.0,
        ),
        MarketQuote(
            symbol="BTC",
            name="Bitcoin",
            price=100_000,
            change_percent=-2.0,
        ),
    )

    snapshot = MarketService().build_snapshot(
        quotes,
        vix=30,
        timestamp=datetime.now(timezone.utc),
    )

    assert snapshot.market_mood == "negative"
    assert snapshot.volatility == "high"
    assert snapshot.summary == (
        "Markets are under pressure and volatility is high."
    )


def test_empty_quotes_are_neutral():
    snapshot = MarketService().build_snapshot(
        (),
        vix=None,
        timestamp=datetime.now(timezone.utc),
    )

    assert snapshot.market_mood == "neutral"
    assert snapshot.volatility == "unknown"