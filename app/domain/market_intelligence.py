from dataclasses import dataclass

from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


@dataclass(frozen=True)
class MarketIntelligence:
    market: MarketSnapshot
    sentiment: SentimentSnapshot
    outlook: str
    confidence: int
    summary: str
