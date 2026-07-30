from datetime import UTC, datetime

from app.domain.account_snapshot import AccountSnapshot
from app.services.portfolio_service import PortfolioService


def test_empty_invested_portfolio_is_all_cash():
    account = AccountSnapshot(
        broker="eToro",
        mode="demo",
        connected=True,
        positions_count=0,
        positions=(),
        pending_orders=0,
        copy_portfolios=0,
        latency_ms=100,
        timestamp=datetime.now(UTC),
        cash_usd=100_000,
        invested_usd=0,
        unrealized_pnl_usd=0,
        equity_usd=100_000,
    )

    portfolio = PortfolioService().analyze(account)

    assert portfolio.total_value == 100_000
    assert portfolio.positions == 0
    assert portfolio.allocation.cash == 100.0
    assert portfolio.allocation.unclassified == 0.0
    assert portfolio.risk_flags == ("Cash concentration",)


def test_invested_assets_remain_unclassified_until_metadata_exists():
    account = AccountSnapshot(
        broker="eToro",
        mode="demo",
        connected=True,
        positions_count=2,
        positions=(),
        pending_orders=0,
        copy_portfolios=0,
        latency_ms=100,
        timestamp=datetime.now(UTC),
        cash_usd=20_000,
        invested_usd=80_000,
        unrealized_pnl_usd=0,
        equity_usd=100_000,
    )

    portfolio = PortfolioService().analyze(account)

    assert portfolio.allocation.cash == 20.0
    assert portfolio.allocation.unclassified == 80.0
    assert portfolio.positions == 2
    assert (
        "Invested assets are not yet classified by asset type" in portfolio.risk_flags
    )
