from datetime import datetime

from app.domain.market_snapshot import MarketQuote, MarketSnapshot


class MarketService:
    POSITIVE_THRESHOLD = 0.25
    NEGATIVE_THRESHOLD = -0.25

    def build_snapshot(
        self,
        quotes: tuple[MarketQuote, ...],
        *,
        vix: float | None = None,
        timestamp: datetime,
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
