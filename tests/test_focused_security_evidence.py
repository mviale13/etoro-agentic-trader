"""Evidencing the security the caller actually asked about."""

from dataclasses import replace

import pytest

from app.application.brain.perception.security_perception import (
    SecurityPerception,
)
from app.domain.company_recommendation import CompanyRecommendation
from app.domain.company_signals import CompanySignals
from app.domain.momentum_signal import MomentumSignal
from app.domain.quality_signal import QualitySignal
from app.domain.value_signal import ValueSignal
from app.domain.watchlist_item import WatchlistItem
from tests.test_brain_context import make_portfolio


def watchlist_item(instrument_id: int, symbol: str) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=f"{symbol} Inc",
        asset_type_id=5,
        asset_type_subcategory_id=0,
        exchange_id=4,
        rank=0,
        avatar_url=None,
    )


class ResolverStub:
    def __init__(self, *symbols: str) -> None:
        self._items = {
            index: watchlist_item(index, symbol)
            for index, symbol in enumerate(symbols, start=1)
        }

    async def items(self) -> dict[int, WatchlistItem]:
        return self._items


class SignalStub:
    def __init__(self) -> None:
        self.built: list[str] = []

    async def build(self, item: WatchlistItem) -> CompanySignals:
        self.built.append(item.symbol)

        return CompanySignals(
            value=ValueSignal(valuation="CHEAP", confidence=70, evidence=()),
            quality=QualitySignal(quality="HIGH", confidence=70, evidence=()),
            momentum=MomentumSignal(
                trend="BULLISH",
                strength="STRONG",
                confidence=70,
                evidence=(),
            ),
        )


def perception(*symbols: str) -> tuple[SecurityPerception, SignalStub]:
    signals = SignalStub()

    return (
        SecurityPerception(
            symbol_resolver=ResolverStub(*symbols),  # type: ignore[arg-type]
            signal_service=signals,  # type: ignore[arg-type]
        ),
        signals,
    )


@pytest.mark.anyio
async def test_the_symbol_asked_about_is_evidenced_without_a_research_budget() -> None:
    """
    `movrvest evaluate UUUU` used to decide without ever looking at UUUU.

    The account holds nothing and the command asks for no candidate
    budget, so per-security perception returned nothing and the Artificial
    CIO judged the security on portfolio and market context alone.
    """

    security, signals = perception("UUUU", "MSFT")

    evidence = await security.execute(
        make_portfolio(),
        candidates=(),
        candidate_limit=0,
        focus_symbols=("UUUU",),
    )

    assert signals.built == ["UUUU"]
    assert isinstance(evidence["UUUU"][0], CompanyRecommendation)


@pytest.mark.anyio
async def test_a_focused_symbol_is_not_evidenced_twice() -> None:
    """It costs a provider request; asking about a holding is not a reason."""

    from app.domain.portfolio_position import PortfolioPosition

    portfolio = replace(
        make_portfolio(),
        holdings=(
            PortfolioPosition(
                symbol="MSFT",
                quantity=1.0,
                invested_usd=100.0,
                market_value_usd=100.0,
                unrealized_pnl_usd=0.0,
                instrument_id=2,
            ),
        ),
    )

    security, signals = perception("UUUU", "MSFT")

    await security.execute(portfolio, focus_symbols=("MSFT",))

    assert signals.built == ["MSFT"]


@pytest.mark.anyio
async def test_a_symbol_no_watchlist_names_produces_no_evidence() -> None:
    """The gap is reported as missing evidence, not filled in."""

    security, signals = perception("UUUU")

    assert await security.execute(make_portfolio(), focus_symbols=("ZZZZ",)) == {}
    assert signals.built == []
