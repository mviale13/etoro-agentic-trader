from collections.abc import Mapping
from dataclasses import dataclass, field

from app.cio.investment_case import InvestmentCase
from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_snapshot import MarketSnapshot
from app.domain.portfolio_snapshot import PortfolioSnapshot


@dataclass(frozen=True, slots=True)
class BrainContext:
    """
    Complete working memory available to MOVRvest reasoning components.

    BrainContext contains facts and previously produced conclusions only.
    It must not contain services, repositories, providers, or API clients.
    """

    portfolio: PortfolioSnapshot
    market: MarketSnapshot
    investment_policy: InvestmentPolicy

    investment_cases: Mapping[str, InvestmentCase] = field(
        default_factory=dict,
    )
    evidence: Mapping[str, tuple[object, ...]] = field(
        default_factory=dict,
    )
    committee_opinions: Mapping[str, tuple[object, ...]] = field(
        default_factory=dict,
    )
    memory: Mapping[str, object] = field(
        default_factory=dict,
    )
    alerts: tuple[str, ...] = ()

    def investment_case(self, symbol: str) -> InvestmentCase | None:
        """Return the investment case for a normalized market symbol."""

        return self.investment_cases.get(symbol.upper().strip())

    def evidence_for(self, symbol: str) -> tuple[object, ...]:
        """Return all available evidence for a normalized market symbol."""

        return self.evidence.get(symbol.upper().strip(), ())

    def opinions_for(self, symbol: str) -> tuple[object, ...]:
        """Return all committee opinions for a normalized market symbol."""

        return self.committee_opinions.get(symbol.upper().strip(), ())
