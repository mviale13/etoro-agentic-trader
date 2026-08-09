"""Canonical market perception."""

from datetime import UTC, datetime
from typing import Protocol

from app.application.market import MarketSnapshotArchive
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


class MarketArchive(Protocol):
    """Anything that keeps what the market read."""

    def record(self, snapshot: MarketSnapshot) -> object: ...


class MarketPerception:
    """
    Produces the current market perception.

    Responsibilities
    ----------------
    - Collect market facts from the infrastructure layer.
    - Build the canonical MarketSnapshot.
    - Record what was observed, so a later cycle can say what moved.
    - Perform no reasoning.
    - Perform no executive decision making.

    Recording belongs here because this is where market facts enter the
    platform, exactly as `EtoroClient` keeps every response that comes
    through its own door. Before it, a quote lived fifteen minutes in a
    cache and was gone, and no question about the market beginning "since"
    could be answered.
    """

    def __init__(
        self,
        provider: MarketDataProvider | None = None,
        market_service: MarketService | None = None,
        sentiment_provider: SentimentProvider | None = None,
        archive: MarketArchive | None = None,
    ) -> None:
        # The read-only door: this runs on every page view, and the market
        # strip is not a reason to make one wait on a provider. What was
        # acquired is served with the moment it was taken.
        self._provider = provider or CachedMarketProvider.stored()
        self._market_service = market_service or MarketService()
        self._sentiment_provider = sentiment_provider or CryptoFearGreedProvider()
        self._archive = archive or MarketSnapshotArchive()

    async def execute(self) -> MarketSnapshot:
        market_data = await self._provider.snapshot()

        snapshot = self._market_service.build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            # Not `utcnow()`, which returns a naive datetime and cannot be
            # compared with the aware ones every reading carries.
            timestamp=datetime.now(UTC),
            sentiment=await self._sentiment(),
        )

        self._record(snapshot)

        return snapshot

    def _record(
        self,
        snapshot: MarketSnapshot,
    ) -> None:
        """
        Keep this observation, or carry on without it.

        An archive that cannot be written to costs the record, not the
        cycle. The investor asked what the market is doing; a full disk is
        not a reason to refuse to answer, and the failure to record is
        visible as a gap in the series rather than hidden behind a
        fabricated entry.
        """

        try:
            self._archive.record(snapshot)
        except OSError:
            return

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
