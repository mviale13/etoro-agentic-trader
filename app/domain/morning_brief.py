
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MorningBrief:
    portfolio_health: str
    portfolio_value: float
    cash_allocation: float
    open_positions: int
    recommendation: str
    confidence: int
    summary: str