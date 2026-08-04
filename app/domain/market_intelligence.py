from dataclasses import dataclass

from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


@dataclass(frozen=True)
class MarketIntelligence:
    market: MarketSnapshot

    #: None when the sentiment index could not be read. The outlook is
    #: then reached on market conditions alone, and says so.
    sentiment: SentimentSnapshot | None
    outlook: str
    confidence: int
    summary: str
