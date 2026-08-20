from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MorningBrief:
    portfolio_health: str
    portfolio_value: float
    #: None where the broker stated no cash figure.
    cash_allocation: float | None
    open_positions: int
    recommendation: str
    confidence: int
    summary: str
