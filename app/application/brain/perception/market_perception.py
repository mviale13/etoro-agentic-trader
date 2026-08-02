"""Canonical market perception."""

from datetime import datetime
from typing import Protocol

from app.application.services.market_service import MarketService
from app.domain.market_snapshot import MarketData, MarketSnapshot
from app.providers.cached_market_provider import CachedMarketProvider


class MarketDataProvider(Protocol):
    """Anything that can price the market, cached or direct."""

    async def snapshot(self) -> MarketData: ...


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
        provider: MarketDataProvider | None = None,
        market_service: MarketService | None = None,
    ) -> None:
        self._provider = provider or CachedMarketProvider()
        self._market_service = market_service or MarketService()

    async def execute(self) -> MarketSnapshot:
        market_data = await self._provider.snapshot()

        return self._market_service.build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            timestamp=datetime.utcnow(),
        )
