"""Application service for constructing a market snapshot."""

from datetime import datetime

from app.domain.market_snapshot import MarketQuote, MarketSnapshot
from app.domain.provenance import least_reliable
from app.domain.sentiment_snapshot import SentimentSnapshot


class MarketService:
    """Build a domain market snapshot from already collected market facts.

    This service belongs to the application layer because it orchestrates a
    use case using domain objects. It performs no I/O and has no presentation
    responsibilities.
    """

    POSITIVE_THRESHOLD = 0.25
    NEGATIVE_THRESHOLD = -0.25

    def build_snapshot(
        self,
        quotes: tuple[MarketQuote, ...],
        *,
        vix: float | None = None,
        timestamp: datetime,
        sentiment: SentimentSnapshot | None = None,
    ) -> MarketSnapshot:
        market_mood = self.classify_market_mood(quotes)
        volatility = self.classify_volatility(vix)
        summary = self.build_summary(market_mood, volatility)

        return MarketSnapshot(
            quotes=quotes,
            market_mood=market_mood,
            volatility=volatility,
            summary=summary,
            timestamp=timestamp,
            vix=vix,
            # The reading that most qualifies everything read off these
            # quotes. A provider that did not answer outranks a merely
            # older one, which is why this is not simply the oldest.
            reading=least_reliable(*(quote.reading for quote in quotes)),
            # Carried, never folded into the mood. The mood is what nine
            # instruments did; sentiment is what one asset class feels,
            # and averaging the two would let each stand in for the other.
            sentiment=sentiment,
        )

    def classify_market_mood(
        self,
        quotes: tuple[MarketQuote, ...],
    ) -> str:
        if not quotes:
            return "neutral"

        average_change = sum(quote.change_percent for quote in quotes) / len(quotes)

        if average_change >= self.POSITIVE_THRESHOLD:
            return "positive"

        if average_change <= self.NEGATIVE_THRESHOLD:
            return "negative"

        return "neutral"

    @staticmethod
    def classify_volatility(vix: float | None) -> str:
        if vix is None:
            return "unknown"

        if vix < 15:
            return "low"

        if vix <= 25:
            return "medium"

        return "high"

    @staticmethod
    def build_summary(
        market_mood: str,
        volatility: str,
    ) -> str:
        if market_mood == "positive" and volatility == "low":
            return "Markets are positive and volatility is low."

        if market_mood == "negative" and volatility == "high":
            return "Markets are under pressure and volatility is high."

        if market_mood == "positive":
            return "Markets are broadly positive today."

        if market_mood == "negative":
            return "Markets are broadly negative today."

        if volatility == "high":
            return "Markets are mixed and volatility is elevated."

        return "Markets are broadly neutral today."
