import asyncio
from datetime import datetime, timezone

from app.domain.account_snapshot import AccountSnapshot
from app.services.account_service import AccountService


class FakeBroker:
    async def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            broker="Fake",
            mode="demo",
            connected=True,
            positions=2,
            pending_orders=1,
            copy_portfolios=0,
            latency_ms=12.5,
            timestamp=datetime.now(timezone.utc),
            cash_usd=900,
            invested_usd=100,
            unrealized_pnl_usd=5,
            equity_usd=1005,
        )


def test_account_service_returns_snapshot():
    snapshot = asyncio.run(AccountService(FakeBroker()).snapshot())
    assert snapshot.connected
    assert snapshot.equity_usd == 1005


def test_account_service_health():
    assert asyncio.run(AccountService(FakeBroker()).health())
