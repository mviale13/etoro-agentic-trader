from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


class MarketIntelligenceService:
    def build(
        self,
        market: MarketSnapshot,
        sentiment: SentimentSnapshot | None,
    ) -> MarketIntelligence:
        """
        Combine market conditions with published crypto sentiment.

        Both readings agreeing is what earns the higher confidence here.
        With sentiment unavailable there is nothing to agree, so the
        outlook rests on market conditions alone and reports that — rather
        than claiming a confirmation that was never observed.
        """

        if sentiment is None:
            return MarketIntelligence(
                market=market,
                sentiment=None,
                outlook=self._market_outlook(market),
                confidence=50,
                summary=(
                    "Crypto sentiment could not be read, so this outlook "
                    "rests on market conditions alone."
                ),
            )

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

    @staticmethod
    def _market_outlook(market: MarketSnapshot) -> str:
        """The outlook market conditions support on their own."""

        if market.market_mood == "positive":
            return "BULLISH"

        if market.market_mood == "negative":
            return "BEARISH"

        return "NEUTRAL"
