from dataclasses import dataclass

from app.domain.investment_policy import InvestmentPolicy
from app.domain.market_intelligence import MarketIntelligence
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.valuation_snapshot import ValuationSnapshot


@dataclass(frozen=True)
class CommitteeContext:
    intelligence: MarketIntelligence
    portfolio: PortfolioSnapshot
    policy: InvestmentPolicy
    valuation: ValuationSnapshot | None = None
