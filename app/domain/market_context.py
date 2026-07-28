from dataclasses import dataclass


@dataclass(frozen=True)
class MarketContext:
    regime: str
    volatility: str
    sentiment: str
    headline: str
