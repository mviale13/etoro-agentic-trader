from app.domain.market_context import MarketContext


class MarketContextService:
    def build(self) -> MarketContext:
        return MarketContext(
            regime="Bullish",
            volatility="Low",
            sentiment="Greed",
            headline=("AI infrastructure continues to lead the market."),
        )
