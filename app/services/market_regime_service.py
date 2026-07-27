from app.domain.market_intelligence import MarketIntelligence
from app.domain.market_regime import MarketRegime, MarketRegimeType


class MarketRegimeService:
    def detect(
        self,
        intelligence: MarketIntelligence,
    ) -> MarketRegime:
        if intelligence.outlook == "BULLISH":
            return MarketRegime(
                regime=MarketRegimeType.BULL,
                confidence=intelligence.confidence,
                summary=("Positive market conditions indicate a bull regime."),
            )

        if intelligence.outlook == "BEARISH":
            return MarketRegime(
                regime=MarketRegimeType.BEAR,
                confidence=intelligence.confidence,
                summary=("Negative market conditions indicate a bear regime."),
            )

        return MarketRegime(
            regime=MarketRegimeType.SIDEWAYS,
            confidence=intelligence.confidence,
            summary=("Mixed market conditions indicate a sideways regime."),
        )
