from dataclasses import dataclass

from app.domain.market_regime import MarketRegimeType


@dataclass(frozen=True, slots=True)
class RegimeMemberPerformance:
    member: str
    regime: MarketRegimeType
    completed: int
    successful: int
    accuracy: int
