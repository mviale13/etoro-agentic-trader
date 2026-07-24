from datetime import datetime, timezone

from app.domain.market_snapshot import MarketQuote, MarketSnapshot


def test_market_snapshot_returns_quote_by_symbol():
    snapshot = MarketSnapshot(
        quotes=(
            MarketQuote(
                symbol="BTC",
                name="Bitcoin",
                price=100_000,
                change_percent=2.5,
            ),
            MarketQuote(
                symbol="SPY",
                name="S&P 500 ETF",
                price=600,
                change_percent=0.4,
            ),
        ),
        market_mood="positive",
        volatility="low",
        summary="Markets are positive and volatility is low.",
        timestamp=datetime.now(timezone.utc),
    )

    bitcoin = snapshot.quote("btc")

    assert bitcoin is not None
    assert bitcoin.name == "Bitcoin"
    assert bitcoin.change_percent == 2.5


def test_market_snapshot_returns_none_for_unknown_symbol():
    snapshot = MarketSnapshot(
        quotes=(),
        market_mood="neutral",
        volatility="unknown",
        summary="Markets are broadly neutral today.",
        timestamp=datetime.now(timezone.utc),
    )

    assert snapshot.quote("UNKNOWN") is None