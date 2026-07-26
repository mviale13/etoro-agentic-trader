from dataclasses import dataclass

from app.domain.portfolio_health import PortfolioHealth
from app.domain.recommendation import Recommendation


@dataclass(frozen=True)
class BriefSnapshot:
    greeting: str
    health: PortfolioHealth
    recommendation: Recommendation
    changes: tuple[str, ...]
    summary: str
    next_action: str
