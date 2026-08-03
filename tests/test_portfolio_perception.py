"""Tests for portfolio perception."""

import inspect
from typing import cast

import pytest

from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_position import PortfolioPosition
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.domain.watchlist_item import WatchlistItem
from app.services.account_service import AccountService
from app.services.instrument_symbol_resolver import (
    InstrumentSymbolResolver,
)
from app.services.portfolio_service import PortfolioService


def make_snapshot(
    holdings: tuple[PortfolioPosition, ...] = (),
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        allocation=Allocation(
            cash=50.0,
            stocks=50.0,
            etfs=0.0,
            crypto=0.0,
            unclassified=0.0,
        ),
        total_value=1_000.0,
        positions=len(holdings),
        largest_position=None,
        largest_position_pct=0.0,
        risk_flags=(),
        holdings=holdings,
    )


def make_holding(
    instrument_id: int,
    market_value_usd: float = 100.0,
) -> PortfolioPosition:
    return PortfolioPosition(
        symbol="",
        quantity=1.0,
        invested_usd=market_value_usd,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=0.0,
        instrument_id=instrument_id,
    )


def make_watchlist_item(
    instrument_id: int,
    symbol: str,
) -> WatchlistItem:
    return WatchlistItem(
        instrument_id=instrument_id,
        symbol=symbol,
        name=symbol,
        asset_type_id=1,
        asset_type_subcategory_id=1,
        exchange_id=1,
        rank=1,
        avatar_url=None,
    )


class ResolverStub:
    def __init__(self, instruments: dict[int, WatchlistItem]) -> None:
        self._instruments = instruments

    async def items(self) -> dict[int, WatchlistItem]:
        return self._instruments

    @staticmethod
    def placeholder(instrument_id: int) -> str:
        return f"#{instrument_id}"


def build_perception(
    snapshot: PortfolioSnapshot,
    instruments: dict[int, WatchlistItem] | None = None,
) -> PortfolioPerception:
    account = cast(AccountSnapshot, object())

    class AccountServiceStub:
        async def snapshot(self) -> AccountSnapshot:
            return account

    class PortfolioServiceStub:
        def analyze(self, received_account: AccountSnapshot) -> PortfolioSnapshot:
            assert received_account is account
            return snapshot

        def allocate(self, resolved: PortfolioSnapshot) -> PortfolioSnapshot:
            return PortfolioService.allocate(resolved)

    return PortfolioPerception(
        account_service=cast(AccountService, AccountServiceStub()),
        portfolio_service=cast(PortfolioService, PortfolioServiceStub()),
        symbol_resolver=cast(
            InstrumentSymbolResolver,
            ResolverStub(instruments or {}),
        ),
    )


def test_portfolio_perception_is_defined_in_perception_layer() -> None:
    assert PortfolioPerception.__module__ == (
        "app.application.brain.perception.portfolio_perception"
    )


def test_portfolio_perception_execute_is_async() -> None:
    assert inspect.iscoroutinefunction(PortfolioPerception.execute)


@pytest.mark.anyio
async def test_portfolio_perception_builds_portfolio_from_account() -> None:
    snapshot = make_snapshot()

    result = await build_perception(snapshot).execute()

    assert result is snapshot


@pytest.mark.anyio
async def test_portfolio_perception_names_each_holding() -> None:
    snapshot = make_snapshot(
        holdings=(
            make_holding(1003, market_value_usd=250.0),
            make_holding(1016, market_value_usd=100.0),
        )
    )

    perception = build_perception(
        snapshot,
        instruments={
            1003: make_watchlist_item(1003, "META"),
            1016: make_watchlist_item(1016, "DIS"),
        },
    )

    result = await perception.execute()

    assert [holding.symbol for holding in result.holdings] == ["META", "DIS"]
    assert all(holding.is_resolved for holding in result.holdings)

    # The largest holding is now named rather than reported as unknown.
    assert result.largest_position == "META"


@pytest.mark.anyio
async def test_portfolio_perception_keeps_unknown_instruments_visible() -> None:
    snapshot = make_snapshot(
        holdings=(make_holding(1238),),
    )

    result = await build_perception(snapshot).execute()

    holding = result.holdings[0]

    # The holding is kept, and its unresolved identity stays obvious.
    assert holding.symbol == "#1238"
    assert not holding.is_resolved
