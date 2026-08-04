from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Opportunity:
    symbol: str
    action: str
    score: float

    policy_fit: float
    committee_confidence: float
    market_score: float
    diversification_score: float

    reason: str
