from dataclasses import dataclass


@dataclass(frozen=True)
class MarketIntelligence:
    market_mood: str
    volatility: str

    fear_greed: int

    vix: float
    treasury_10y: float
    gold_change: float
    oil_change: float
    dollar_index: float

    summary: str
