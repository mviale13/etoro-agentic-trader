from app.analysts.market.equity_trend_analyst import EquityTrendAnalyst
from app.analysts.market.market_breadth_analyst import MarketBreadthAnalyst
from app.domain.market_facts import MarketFacts
from app.domain.market_research import MarketResearch


class MarketResearchService:
    """Run all market analysts and assemble MarketResearch."""

    def __init__(self) -> None:
        self._equity_trend_analyst = EquityTrendAnalyst()
        self._market_breadth_analyst = MarketBreadthAnalyst()

    def analyze(
        self,
        facts: MarketFacts,
    ) -> MarketResearch:
        return MarketResearch(
            equity_trend=self._equity_trend_analyst.analyze(facts),
            market_breadth=self._market_breadth_analyst.analyze(facts),
        )
