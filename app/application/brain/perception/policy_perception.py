"""Policy perception component."""

from app.domain.investment_policy import InvestmentPolicy
from app.services.investor_strategy_service import (
    InvestorStrategyService,
)


class PolicyPerception:
    """Produces the active investment policy."""

    def __init__(
        self,
        strategy_service: InvestorStrategyService | None = None,
    ) -> None:
        self._strategy_service = strategy_service or InvestorStrategyService()

    def execute(self) -> InvestmentPolicy | None:
        return self._strategy_service.load_policy()
