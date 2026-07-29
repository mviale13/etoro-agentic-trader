"""Tests for portfolio perception."""

import inspect
from typing import cast

import pytest

from app.application.brain.perception.portfolio_perception import (
    PortfolioPerception,
)
from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.services.account_service import AccountService
from app.services.portfolio_service import PortfolioService


def test_portfolio_perception_is_defined_in_perception_layer() -> None:
    assert PortfolioPerception.__module__ == (
        "app.application.brain.perception.portfolio_perception"
    )


def test_portfolio_perception_execute_is_async() -> None:
    assert inspect.iscoroutinefunction(PortfolioPerception.execute)


@pytest.mark.anyio
async def test_portfolio_perception_builds_portfolio_from_account() -> None:
    account = cast(AccountSnapshot, object())
    portfolio = cast(PortfolioSnapshot, object())
    calls: list[str] = []

    class AccountServiceStub:
        async def snapshot(self) -> AccountSnapshot:
            calls.append("account")
            return account

    class PortfolioServiceStub:
        def analyze(self, received_account: AccountSnapshot) -> PortfolioSnapshot:
            calls.append("portfolio")
            assert received_account is account
            return portfolio

    perception = PortfolioPerception(
        account_service=cast(AccountService, AccountServiceStub()),
        portfolio_service=cast(PortfolioService, PortfolioServiceStub()),
    )

    result = await perception.execute()

    assert result is portfolio
    assert calls == ["account", "portfolio"]
