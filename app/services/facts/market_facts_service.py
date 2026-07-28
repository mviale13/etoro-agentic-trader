from datetime import UTC, datetime
from typing import Protocol

from app.domain.market_facts import (
    MarketFact,
    MarketFacts,
)
from app.domain.market_snapshot import MarketData
from app.providers.yahoo_market_provider import (
    YahooMarketProvider,
)


class MarketDataProvider(Protocol):
    async def snapshot(
        self,
    ) -> MarketData: ...


class MarketFactsService:
    def __init__(
        self,
        provider: MarketDataProvider | None = None,
    ) -> None:
        self._provider = provider or YahooMarketProvider()

    async def build(
        self,
    ) -> MarketFacts:
        data = await self._provider.snapshot()
        timestamp = datetime.now(UTC)

        instruments = tuple(
            MarketFact(
                symbol=quote.symbol,
                name=quote.name,
                price=quote.price,
                change_percent=(quote.change_percent),
                source="Yahoo Finance",
                as_of=timestamp,
            )
            for quote in data.quotes
        )

        return MarketFacts(
            instruments=instruments,
            vix=data.vix,
            source="Yahoo Finance",
            as_of=timestamp,
        )
