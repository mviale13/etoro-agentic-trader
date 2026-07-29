from dataclasses import dataclass

from app.domain.equity_trend_opinion import EquityTrendOpinion
from app.domain.market_breadth_opinion import MarketBreadthOpinion


@dataclass(frozen=True, slots=True)
class MarketResearch:
    """Aggregates all market specialist opinions."""

    equity_trend: EquityTrendOpinion
    market_breadth: MarketBreadthOpinion
