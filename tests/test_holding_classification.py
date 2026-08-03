"""Knowing what the account actually holds."""

from dataclasses import replace

from app.application.brain.reasoning.behavior_analyst import BehaviorAnalyst
from app.brain import BrainBuilder
from app.domain.investment_policy import (
    AllocationTarget,
    InvestmentConstraints,
    InvestmentPolicy,
)
from app.domain.portfolio_position import PortfolioPosition
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.services.portfolio_service import PortfolioService
from tests.test_brain_context import make_market


def holding(
    symbol: str,
    market_value_usd: float,
    asset_class: str | None,
) -> PortfolioPosition:
    return PortfolioPosition(
        symbol=symbol,
        quantity=1.0,
        invested_usd=market_value_usd,
        market_value_usd=market_value_usd,
        unrealized_pnl_usd=0.0,
        asset_class=asset_class,
    )


def snapshot(*holdings: PortfolioPosition) -> PortfolioSnapshot:
    invested = sum(item.market_value_usd for item in holdings)

    return PortfolioSnapshot(
        allocation=Allocation(
            cash=100.0 - invested / 1000.0,
            stocks=0.0,
            etfs=0.0,
            crypto=0.0,
            unclassified=invested / 1000.0,
        ),
        total_value=100_000.0,
        positions=len(holdings),
        largest_position=holdings[0].symbol if holdings else None,
        largest_position_pct=0.0,
        risk_flags=("Invested assets are not yet classified by asset type",),
        holdings=holdings,
    )


def test_the_account_reports_what_it_holds() -> None:
    """
    Every invested euro used to sit in `unclassified`.

    The watchlists carried each instrument's eToro asset type the whole
    time; nothing joined it onto the holdings, so the policy's stock, ETF
    and crypto targets had nothing to be measured against.
    """

    allocated = PortfolioService.allocate(
        snapshot(
            holding("MSFT", 30_000.0, "stock"),
            holding("IB01.L", 10_000.0, "etf"),
            holding("BTC", 20_000.0, "crypto"),
        )
    )

    assert allocated.allocation.stocks == 30.0
    assert allocated.allocation.etfs == 10.0
    assert allocated.allocation.crypto == 20.0
    assert allocated.allocation.unclassified == 0.0


def test_the_standing_flag_goes_once_the_holdings_are_known() -> None:
    allocated = PortfolioService.allocate(snapshot(holding("MSFT", 30_000.0, "stock")))

    assert allocated.risk_flags == ()


def test_what_cannot_be_classified_says_how_much() -> None:
    """
    A holding no watchlist describes is not quietly counted somewhere.

    Nor is a commodity: the policy sets no commodity target, so it cannot
    be reported as drifting from one.
    """

    allocated = PortfolioService.allocate(
        snapshot(
            holding("MSFT", 30_000.0, "stock"),
            holding("#4821", 5_000.0, None),
            holding("COCOA.FUT", 5_000.0, "commodity"),
        )
    )

    assert allocated.allocation.stocks == 30.0
    assert allocated.allocation.unclassified == 10.0
    assert any("cannot classify" in flag for flag in allocated.risk_flags)


def policy(max_crypto: float) -> InvestmentPolicy:
    return InvestmentPolicy(
        risk_profile="balanced",
        target=AllocationTarget(stocks=50.0, etfs=25.0, crypto=20.0, cash=5.0),
        constraints=InvestmentConstraints(
            max_single_position=90.0,
            max_crypto=max_crypto,
            rebalance_threshold=95.0,
        ),
    )


def alignment(portfolio: PortfolioSnapshot, max_crypto: float) -> float:
    brain = BrainBuilder(
        portfolio=portfolio,
        market=make_market(),
        investment_policy=policy(max_crypto),
    ).build()

    return BehaviorAnalyst().assess(brain).policy_alignment_score


def test_crypto_beyond_the_policy_ceiling_is_scored() -> None:
    """The limit was unenforceable while nothing knew what was crypto."""

    portfolio = PortfolioService.allocate(
        snapshot(
            holding("BTC", 60_000.0, "crypto"),
            holding("MSFT", 40_000.0, "stock"),
        )
    )

    assert alignment(portfolio, max_crypto=20.0) < alignment(portfolio, max_crypto=65.0)


def test_an_unclassifiable_account_is_not_scored_against_the_crypto_limit() -> None:
    """
    The share below the ceiling would be understated by exactly the part
    nobody could identify, so the limit is left unmeasured instead.
    """

    partly_known = PortfolioService.allocate(
        snapshot(
            holding("BTC", 60_000.0, "crypto"),
            holding("#4821", 40_000.0, None),
        )
    )

    assert partly_known.allocation.unclassified == 40.0
    assert alignment(partly_known, max_crypto=20.0) == alignment(
        partly_known,
        max_crypto=65.0,
    )


def test_an_empty_account_is_left_alone() -> None:
    empty = replace(snapshot(), total_value=0.0)

    assert PortfolioService.allocate(empty) is empty
