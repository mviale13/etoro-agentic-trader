"""Portfolio perception component for the MOVRvest investment brain."""

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.services.account_service import AccountService
from app.services.portfolio_service import PortfolioService


class PortfolioPerception:
    """Collect and interpret the investor's current portfolio."""

    def __init__(
        self,
        account_service: AccountService | None = None,
        portfolio_service: PortfolioService | None = None,
    ) -> None:
        self._account_service = account_service or AccountService(
            EtoroAccountBroker(Settings())
        )
        self._portfolio_service = portfolio_service or PortfolioService()

    async def execute(self) -> PortfolioSnapshot:
        """Build the current portfolio snapshot from broker account data."""
        account = await self._account_service.snapshot()

        return self._portfolio_service.analyze(account)
