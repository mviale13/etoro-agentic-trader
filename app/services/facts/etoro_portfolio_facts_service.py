from typing import Protocol

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.domain.account_snapshot import AccountSnapshot
from app.domain.portfolio_facts import PortfolioFacts
from app.services.account_service import AccountService
from app.services.portfolio_service import PortfolioService


class AccountSnapshotProvider(Protocol):
    async def snapshot(
        self,
    ) -> AccountSnapshot: ...


class EtoroPortfolioFactsService:
    def __init__(
        self,
        account_provider: AccountSnapshotProvider | None = None,
    ) -> None:
        self._account_provider = account_provider or AccountService(
            EtoroAccountBroker(
                Settings(),
            ),
        )

    async def build(
        self,
    ) -> PortfolioFacts:
        account = await self._account_provider.snapshot()

        portfolio = PortfolioService().analyze(
            account,
        )

        return PortfolioFacts(
            total_value_usd=(account.equity_usd or 0.0),
            total_value_eur=(portfolio.total_value_eur),
            cash_usd=(account.cash_usd or 0.0),
            invested_usd=(account.invested_usd or 0.0),
            unrealized_pnl_usd=(account.unrealized_pnl_usd or 0.0),
            cash_allocation=(portfolio.allocation.cash),
            positions=account.positions,
            pending_orders=(account.pending_orders),
            copy_portfolios=(account.copy_portfolios),
            connected=account.connected,
            latency_ms=account.latency_ms,
            last_sync=account.timestamp,
            source=(f"{account.broker} {account.mode}"),
        )
