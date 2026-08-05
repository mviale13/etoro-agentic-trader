from datetime import UTC, datetime

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
        timestamp=datetime.now(UTC),
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
        timestamp=datetime.now(UTC),
    )

    assert snapshot.quote("UNKNOWN") is None


def make_quote(
    change_percent: float,
    realized_volatility: float | None,
) -> MarketQuote:
    return MarketQuote(
        symbol="TEST",
        name="Test Instrument",
        price=100.0,
        change_percent=change_percent,
        realized_volatility=realized_volatility,
    )


def test_the_typical_day_is_read_off_the_instruments_own_volatility():
    """28% annualised volatility is a 1.76% ordinary day."""

    quote = make_quote(change_percent=1.0, realized_volatility=0.28)

    assert quote.typical_daily_move_pct is not None
    assert round(quote.typical_daily_move_pct, 2) == 1.76


def test_todays_move_is_compared_to_the_instruments_own_day():
    """
    A 2% day is routine for Bitcoin and remarkable for a bond index.

    Only the instrument's own history can say which, so the ratio exists
    per instrument or not at all.
    """

    calm = make_quote(change_percent=-3.6, realized_volatility=0.28)

    assert calm.move_ratio is not None
    assert round(calm.move_ratio, 2) == 2.04
    assert calm.moved_unusually is True

    routine = make_quote(change_percent=1.7, realized_volatility=0.28)

    assert routine.moved_unusually is False


def test_an_unmeasured_history_leaves_the_comparison_absent_not_calm():
    quote = make_quote(change_percent=9.0, realized_volatility=None)

    assert quote.typical_daily_move_pct is None
    assert quote.move_ratio is None
    assert quote.moved_unusually is None
