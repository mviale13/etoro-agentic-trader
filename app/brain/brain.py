from dataclasses import dataclass

from app.brain.brain_context import BrainContext
from app.cio.investment_case import InvestmentCase
from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot


@dataclass(frozen=True, slots=True)
class Brain:
    """
    Stable entry point to the MOVRvest cognitive system.

    The Brain exposes a complete working memory for a single
    investment decision cycle. It contains no infrastructure,
    business logic, or reasoning.
    """

    context: BrainContext

    @property
    def portfolio(self) -> PortfolioSnapshot:
        return self.context.portfolio

    @property
    def market(self) -> MarketSnapshot:
        return self.context.market

    @property
    def policy(self) -> InvestmentPolicy:
        """Convenience alias for the investment policy."""
        return self.context.investment_policy

    @property
    def investment_policy(self) -> InvestmentPolicy:
        """
        Backwards-compatible accessor.

        New code should prefer `brain.policy`.
        """
        return self.context.investment_policy

    @property
    def investment_cases(self) -> dict[str, InvestmentCase]:
        return dict(self.context.investment_cases)

    @property
    def memory(self) -> dict[str, object]:
        return dict(self.context.memory)

    @property
    def alerts(self) -> tuple[str, ...]:
        return self.context.alerts

    def investment_case(self, symbol: str) -> InvestmentCase | None:
        """Return the investment case associated with a symbol."""
        return self.context.investment_case(symbol)

    def evidence_for(self, symbol: str) -> tuple[object, ...]:
        """Return all evidence available for a symbol."""
        return self.context.evidence_for(symbol)

    def opinions_for(self, symbol: str) -> tuple[object, ...]:
        """Return all committee opinions available for a symbol."""
        return self.context.opinions_for(symbol)
