"""Canonical market perception."""

from datetime import UTC, datetime
from typing import Protocol

from app.application.services.market_service import MarketService
from app.domain.market_snapshot import MarketData, MarketSnapshot
from app.domain.sentiment_snapshot import SentimentSnapshot
from app.providers.cached_market_provider import CachedMarketProvider
from app.providers.crypto_fear_greed_provider import CryptoFearGreedProvider


class MarketDataProvider(Protocol):
    """Anything that can price the market, cached or direct."""

    async def snapshot(self) -> MarketData: ...


class SentimentProvider(Protocol):
    """Anything that publishes a sentiment reading, or nothing."""

    async def snapshot(self) -> SentimentSnapshot | None: ...


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
        sentiment_provider: SentimentProvider | None = None,
    ) -> None:
        self._provider = provider or CachedMarketProvider()
        self._market_service = market_service or MarketService()
        self._sentiment_provider = sentiment_provider or CryptoFearGreedProvider()

    async def execute(self) -> MarketSnapshot:
        market_data = await self._provider.snapshot()

        return self._market_service.build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            # Not `utcnow()`, which returns a naive datetime and cannot be
            # compared with the aware ones every reading carries.
            timestamp=datetime.now(UTC),
            sentiment=await self._sentiment(),
        )

    async def _sentiment(self) -> SentimentSnapshot | None:
        """
        The published sentiment reading, or nothing.

        The Brain has never held one. The only index this platform reads
        lived on the legacy committee path, where it set the outlook for
        the whole market — and the canonical pipeline could not see it at
        all, so the one asset class it does describe was judged without
        it.

        An index that cannot be read costs the reading, not the cycle.
        """

        try:
            return await self._sentiment_provider.snapshot()
        except Exception:
            return None
