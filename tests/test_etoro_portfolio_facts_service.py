import asyncio
from datetime import UTC, datetime

from app.domain.account_snapshot import AccountSnapshot
from app.services.facts.etoro_portfolio_facts_service import (
    EtoroPortfolioFactsService,
)


class FakeAccountProvider:
    async def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            broker="eToro",
            mode="Demo",
            connected=True,
            positions=2,
            pending_orders=1,
            copy_portfolios=0,
            latency_ms=211.3,
            timestamp=datetime(
                2026,
                7,
                28,
                14,
                0,
                tzinfo=UTC,
            ),
            cash_usd=75000.0,
            invested_usd=25000.0,
            unrealized_pnl_usd=500.0,
            equity_usd=100000.0,
        )


def test_builds_portfolio_facts_from_etoro() -> None:
    service = EtoroPortfolioFactsService(
        account_provider=FakeAccountProvider(),
    )

    facts = asyncio.run(
        service.build(),
    )

    assert facts.total_value_usd == 100000.0
    assert facts.cash_usd == 75000.0
    assert facts.invested_usd == 25000.0
    assert facts.unrealized_pnl_usd == 500.0
    assert facts.cash_allocation == 75.0
    assert facts.positions == 2
    assert facts.pending_orders == 1
    assert facts.connected is True
    assert facts.source == "eToro Demo"
