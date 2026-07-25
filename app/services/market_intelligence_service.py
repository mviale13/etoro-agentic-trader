from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


class MarketIntelligenceService:
    def build(
        self,
        market: MarketSnapshot,
        sentiment: SentimentSnapshot,
    ) -> MarketIntelligence:
        if market.market_mood == "positive" and sentiment.score >= 60:
            outlook = "BULLISH"
            confidence = 90
            summary = "Market momentum and crypto sentiment are aligned."

        elif market.market_mood == "negative" and sentiment.score <= 40:
            outlook = "BEARISH"
            confidence = 95
            summary = "Weak market conditions are confirmed by crypto fear."

        else:
            outlook = "NEUTRAL"
            confidence = 60
            summary = "Market and crypto sentiment signals are mixed."

        return MarketIntelligence(
            market=market,
            sentiment=sentiment,
            outlook=outlook,
            confidence=confidence,
            summary=summary,
        )
