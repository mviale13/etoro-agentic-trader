from dataclasses import dataclass

from app.domain.investment_policy import InvestmentPolicy
from app.domain.investor_dna import InvestorDNA
from app.domain.market_context import MarketContext
from app.domain.observation import Observation
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.recommendation import Recommendation


@dataclass(frozen=True)
class BrainContext:
    portfolio: PortfolioSnapshot
    recommendation: Recommendation
    observation: Observation
    investor_dna: InvestorDNA
    market: MarketContext
    investment_policy: InvestmentPolicy | None
