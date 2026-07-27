from dataclasses import dataclass


@dataclass(frozen=True)
class InvestorDNA:
    confidence: int
    prefers_quality: bool
    prefers_diversification: bool
    prefers_value: bool
    avoids_high_volatility: bool
