from dataclasses import dataclass

from app.domain.committee_decision import CommitteeDecision
from app.domain.market_intelligence import MarketIntelligence
from app.domain.portfolio_snapshot import PortfolioSnapshot


@dataclass(frozen=True)
class Recommendation:
    symbol: str
    portfolio: PortfolioSnapshot
    intelligence: MarketIntelligence
    decision: CommitteeDecision
