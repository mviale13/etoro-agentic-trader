from datetime import UTC, datetime

from app.providers.crypto_fear_greed_provider import (
    CryptoFearGreedProvider,
)
from app.providers.yahoo_market_provider import YahooMarketProvider
from app.renderers.intelligence_renderer import IntelligenceRenderer
from app.services.market_intelligence_service import (
    MarketIntelligenceService,
)
from app.services.market_service import MarketService


async def run() -> int:
    yahoo = YahooMarketProvider()
    fear_greed = CryptoFearGreedProvider()

    market_data = await yahoo.snapshot()

    market = MarketService().build_snapshot(
        quotes=market_data.quotes,
        vix=market_data.vix,
        timestamp=datetime.now(UTC),
    )

    sentiment = await fear_greed.snapshot()

    intelligence = MarketIntelligenceService().build(
        market=market,
        sentiment=sentiment,
    )

    IntelligenceRenderer.render(intelligence)

    return 0
