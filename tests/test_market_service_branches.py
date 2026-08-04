from datetime import UTC, datetime

from app.domain.market_snapshot import MarketQuote
from app.services.market_service import MarketService


def build_snapshot(
    *,
    changes: tuple[float, ...],
    vix: float | None,
):
    quotes = tuple(
        MarketQuote(
            symbol=f"T{index}",
            name=f"Test {index}",
            price=100,
            change_percent=change,
        )
        for index, change in enumerate(changes, start=1)
    )

    return MarketService().build_snapshot(
        quotes,
        vix=vix,
        timestamp=datetime.now(UTC),
    )


def test_neutral_market_with_medium_volatility():
    snapshot = build_snapshot(
        changes=(0.1, -0.1),
        vix=20,
    )

    assert snapshot.market_mood == "neutral"
    assert snapshot.volatility == "medium"
    assert snapshot.summary == "Markets are broadly neutral today."


def test_positive_market_with_medium_volatility():
    snapshot = build_snapshot(
        changes=(0.5, 0.5),
        vix=20,
    )

    assert snapshot.market_mood == "positive"
    assert snapshot.volatility == "medium"
    assert snapshot.summary == "Markets are broadly positive today."


def test_negative_market_with_medium_volatility():
    snapshot = build_snapshot(
        changes=(-0.5, -0.5),
        vix=20,
    )

    assert snapshot.market_mood == "negative"
    assert snapshot.volatility == "medium"
    assert snapshot.summary == "Markets are broadly negative today."


def test_neutral_market_with_high_volatility():
    snapshot = build_snapshot(
        changes=(0.1, -0.1),
        vix=30,
    )

    assert snapshot.market_mood == "neutral"
    assert snapshot.volatility == "high"
    assert snapshot.summary == ("Markets are mixed and volatility is elevated.")


def test_unknown_volatility_when_vix_is_missing():
    snapshot = build_snapshot(
        changes=(),
        vix=None,
    )

    assert snapshot.market_mood == "neutral"
    assert snapshot.volatility == "unknown"
