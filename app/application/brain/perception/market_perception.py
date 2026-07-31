"""Canonical market perception."""

from datetime import datetime

from app.application.services.market_service import MarketService
from app.domain.market_snapshot import MarketSnapshot
from app.providers.yahoo_market_provider import YahooMarketProvider


class MarketPerception:
    """
    Produces the current market perception.

    Responsibilities
    ----------------
    - Collect market facts from the infrastructure layer.
    - Build the canonical MarketSnapshot.
    - Perform no reasoning.
    - Perform no executive decision making.
    """

    def __init__(
        self,
        provider: YahooMarketProvider | None = None,
        market_service: MarketService | None = None,
    ) -> None:
        self._provider = provider or YahooMarketProvider()
        self._market_service = market_service or MarketService()

    async def execute(self) -> MarketSnapshot:
        market_data = await self._provider.snapshot()

        return self._market_service.build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            timestamp=datetime.utcnow(),
        )
