"""What the market mood nets out, corner by corner."""

from datetime import UTC, datetime

from app.api.routes.market import _payload
from app.application.services.market_service import MarketService
from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.services.market_breadth_service import MarketBreadthService

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def quote(symbol: str, change_percent: float) -> MarketQuote:
    return MarketQuote(
        symbol=symbol,
        name=symbol,
        price=100.0,
        change_percent=change_percent,
        realized_volatility=0.20,
        reading=Provenance(source="Yahoo Finance", observed_at=NOW),
    )


def market(
    *quotes: MarketQuote,
    vix: float | None = 18.0,
) -> MarketSnapshot:
    """Built the way the Brain builds it, so the test exercises that path."""

    return MarketService().build_snapshot(
        quotes=quotes,
        vix=vix,
        timestamp=NOW,
    )


def everything(
    equity_change: float = 0.8,
    crypto_change: float = 2.0,
    commodity_change: float = 0.1,
    dollar_change: float = 0.1,
    rates_change: float = 0.1,
) -> MarketSnapshot:
    return market(
        quote("SPY", equity_change),
        quote("QQQ", equity_change),
        quote("IWM", equity_change),
        quote("BTC", crypto_change),
        quote("ETH", crypto_change),
        quote("GLD", commodity_change),
        quote("WTI", commodity_change),
        quote("DXY", dollar_change),
        quote("TNX", rates_change),
    )


def test_every_corner_of_the_market_is_classified() -> None:
    breadth = MarketBreadthService().build(everything())

    assert breadth.equities == "positive"
    assert breadth.technology == "positive"
    assert breadth.small_caps == "positive"
    assert breadth.crypto == "positive"
    assert breadth.commodities == "neutral"
    assert breadth.dollar == "neutral"
    assert breadth.rates == "neutral"
    assert breadth.volatility == "medium"


def test_a_defensive_day_reads_as_one() -> None:
    breadth = MarketBreadthService().build(
        everything(
            equity_change=-1.3,
            crypto_change=-3.5,
            commodity_change=1.0,
            dollar_change=0.7,
        )
    )

    assert breadth.equities == "negative"
    assert breadth.crypto == "negative"
    assert breadth.commodities == "positive"
    assert breadth.dollar == "positive"


def test_breadth_says_what_the_market_mood_nets_out() -> None:
    """
    The mood is the average of nine instruments. A crypto rally against
    an equity sell-off reports as neutral, and reports neither.
    """

    snapshot = everything(equity_change=-2.0, crypto_change=2.8)
    breadth = MarketBreadthService().build(snapshot)

    assert snapshot.market_mood == "neutral"

    assert breadth.equities == "negative"
    assert breadth.crypto == "positive"


def test_a_corner_nothing_priced_is_unknown_rather_than_flat() -> None:
    """
    Left out of the picture, a missing group reads as a market that did
    not move. It did not fail to move; nobody looked.
    """

    breadth = MarketBreadthService().build(market(quote("SPY", 1.0)))

    assert breadth.equities == "positive"
    assert breadth.crypto == "unknown"
    assert breadth.commodities == "unknown"
    assert breadth.rates == "unknown"


def test_an_unread_vix_is_unknown_not_calm() -> None:
    unread = MarketBreadthService().build(market(quote("SPY", 1.0), vix=None))

    assert MarketBreadthService().build(everything()).volatility == "medium"
    assert unread.volatility == "unknown"


def test_the_direction_threshold_is_the_one_the_mood_is_drawn_at() -> None:
    """A day that counts as positive for the market is not flat equities."""

    assert MarketBreadthService.POSITIVE_THRESHOLD == MarketService.POSITIVE_THRESHOLD
    assert MarketBreadthService.NEGATIVE_THRESHOLD == MarketService.NEGATIVE_THRESHOLD


def test_the_snapshot_keeps_the_figure_the_band_was_decided_by() -> None:
    """
    The VIX was fetched, turned into an adjective and dropped. An
    adjective cannot be compared with yesterday's adjective.
    """

    snapshot = everything()

    assert snapshot.vix == 18.0
    assert snapshot.volatility == "medium"


def test_the_snapshot_can_say_when_it_was_observed() -> None:
    """
    Its `timestamp` is when the object was assembled, which is not when
    anything in it was seen.
    """

    snapshot = everything()

    assert snapshot.reading is not None
    assert snapshot.reading.source == "Yahoo Finance"
    assert snapshot.reading.observed_at == NOW


def test_the_route_serves_the_mood_and_what_it_hides_together() -> None:
    served = _payload(everything(equity_change=-2.0, crypto_change=2.8))

    assert served["mood"] == "neutral"
    assert served["vix"] == 18.0
    assert isinstance(served["observed"], str)

    breadth = served["breadth"]

    assert isinstance(breadth, dict)
    assert breadth["equities"] == "negative"
    assert breadth["crypto"] == "positive"

    quotes = served["quotes"]

    assert isinstance(quotes, list)
    assert len(quotes) == 9
    assert quotes[0]["symbol"] == "SPY"
    assert quotes[0]["realized_volatility"] == 0.20
