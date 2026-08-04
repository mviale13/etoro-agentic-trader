"""What the market is doing, beside what one asset class feels about it."""

from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_snapshot import MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot


class MarketIntelligenceService:
    """
    State the market outlook, and report sentiment as what it is.

    The outlook used to be a blend. A positive market plus crypto greed
    read BULLISH at 90% confidence; a negative market plus crypto fear
    read BEARISH at 95%, summarised as "weak market conditions are
    confirmed by crypto fear". The only index this platform reads is
    Alternative.me's crypto Fear & Greed, and crypto fear cannot confirm
    an equity sell-off — that is a different asset class having a
    different day. Two readings pointing the same way looked like
    corroboration and were not, and the agreement raised the confidence of
    everything downstream, including the regime that weights the
    committees.

    The outlook now rests on market conditions alone, which is the only
    thing here that describes the whole market. Sentiment is carried
    beside it, named for the asset class it was taken of, so a reader can
    weigh it against the holdings it actually applies to.
    """

    #: The outlook rests on one day's average move across nine
    #: instruments. That is a real reading and a narrow one, and the
    #: confidence says so rather than rising when an unrelated index
    #: happens to agree.
    CONFIDENCE = 50

    def build(
        self,
        market: MarketSnapshot,
        sentiment: SentimentSnapshot | None,
    ) -> MarketIntelligence:
        return MarketIntelligence(
            market=market,
            sentiment=sentiment,
            outlook=self._market_outlook(market),
            confidence=self.CONFIDENCE,
            summary=self._summary(sentiment),
        )

    @staticmethod
    def _summary(
        sentiment: SentimentSnapshot | None,
    ) -> str:
        """What the outlook rests on, and what it does not."""

        statement = (
            "This outlook rests on today's market conditions across the "
            "instruments MOVRvest prices."
        )

        if sentiment is None:
            return f"{statement} No sentiment index could be read."

        return (
            f"{statement} {sentiment.stated}, which describes "
            f"{sentiment.subject.value} and is not evidence about the rest "
            "of the market."
        )

    @staticmethod
    def _market_outlook(market: MarketSnapshot) -> str:
        """The outlook market conditions support on their own."""

        if market.market_mood == "positive":
            return "BULLISH"

        if market.market_mood == "negative":
            return "BEARISH"

        return "NEUTRAL"
