"""Market confidence measures how well evidenced the reading is, not its mood.

The term used to move with how uniformly the instruments moved: a flat market
and one down 8% across the board both read 0.94, and that number is one third
of a cognitive average that gates real decisions. These pin the fix — direction
no longer moves it, and evidence does.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.application.brain.reasoning.market_analyst import MarketAnalyst
from app.application.services.market_service import MarketService
from app.domain.market_snapshot import MarketQuote, MarketSnapshot


def _quote(symbol: str, change_percent: float, measured: bool = True) -> MarketQuote:
    return MarketQuote(
        symbol=symbol,
        name=f"{symbol} tracker",
        price=100.0,
        change_percent=change_percent,
        realized_volatility=0.2 if measured else None,
    )


def _snapshot(*quotes: MarketQuote) -> MarketSnapshot:
    return MarketService().build_snapshot(
        quotes=quotes,
        vix=16.0,
        timestamp=datetime.now(UTC),
    )


PANEL = ("SPY", "QQQ", "IWM", "BTC", "ETH", "GLD", "WTI", "DXY", "TNX")


def _full_panel(change_percent: float) -> MarketSnapshot:
    return _snapshot(*(_quote(symbol, change_percent) for symbol in PANEL))


def test_a_flat_market_and_a_falling_one_are_equally_well_evidenced() -> None:
    """The exact defect: direction must not move the confidence."""

    flat = MarketAnalyst()._assess_snapshot(_full_panel(0.0))
    falling = MarketAnalyst()._assess_snapshot(_full_panel(-8.0))

    assert flat.confidence == falling.confidence


def test_the_full_panel_priced_and_measured_is_fully_evidenced() -> None:
    assert MarketAnalyst()._assess_snapshot(_full_panel(1.0)).confidence == 1.0


def test_a_thin_panel_is_less_evidenced_than_a_full_one() -> None:
    thin = MarketAnalyst()._assess_snapshot(
        _snapshot(_quote("SPY", 1.0), _quote("QQQ", 1.0))
    )
    full = MarketAnalyst()._assess_snapshot(_full_panel(1.0))

    assert thin.confidence < full.confidence


def test_prices_without_their_history_are_only_half_evidenced() -> None:
    """A bare price is weaker evidence than one carrying its year of history."""

    bare = _snapshot(*(_quote(symbol, 1.0, measured=False) for symbol in PANEL))

    assert MarketAnalyst()._assess_snapshot(bare).confidence == 0.5
