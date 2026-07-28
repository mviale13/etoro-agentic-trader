from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpportunityScorecard:
    symbol: str

    momentum: int

    quality: int

    valuation: int

    volatility: int

    liquidity: int

    overall: int
