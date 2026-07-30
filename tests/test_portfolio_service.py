from datetime import UTC, datetime

from app.domain.account_snapshot import AccountSnapshot
from app.services.portfolio_service import PortfolioService


def build_account(
    *,
    equity: float | None,
    cash: float | None,
    invested: float | None,
    positions: int = 0,
) -> AccountSnapshot:
    return AccountSnapshot(
        broker="eToro",
        mode="demo",
        connected=True,
        positions_count=positions,
        positions=(),
        pending_orders=0,
        copy_portfolios=0,
        latency_ms=100,
        timestamp=datetime.now(UTC),
        cash_usd=cash,
        invested_usd=invested,
        unrealized_pnl_usd=0,
        equity_usd=equity,
    )


def test_zero_equity_returns_zero_allocations():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=0,
            cash=0,
            invested=0,
        )
    )

    assert portfolio.total_value == 0
    assert portfolio.allocation.cash == 0
    assert portfolio.allocation.unclassified == 0
    assert portfolio.risk_flags == ()


def test_missing_values_are_treated_as_zero():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=None,
            cash=None,
            invested=None,
        )
    )

    assert portfolio.total_value == 0
    assert portfolio.allocation.cash == 0
    assert portfolio.allocation.unclassified == 0


def test_high_cash_allocation_sets_cash_concentration_flag():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=100_000,
            cash=85_000,
            invested=15_000,
            positions=2,
        )
    )

    assert portfolio.allocation.cash == 85.0
    assert portfolio.allocation.unclassified == 15.0
    assert "Cash concentration" in portfolio.risk_flags
    assert (
        "Invested assets are not yet classified by asset type" in portfolio.risk_flags
    )


def test_percentage_rounding():
    portfolio = PortfolioService().analyze(
        build_account(
            equity=3,
            cash=1,
            invested=2,
        )
    )

    assert portfolio.allocation.cash == 33.33
    assert portfolio.allocation.unclassified == 66.67
