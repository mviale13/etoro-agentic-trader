from datetime import datetime, timezone

from app.providers.yahoo_market_provider import YahooMarketProvider
from app.renderers.market_renderer import MarketRenderer
from app.services.market_service import MarketService


async def run() -> int:
    try:
        market_data = await YahooMarketProvider().snapshot()

        snapshot = MarketService().build_snapshot(
            quotes=market_data.quotes,
            vix=market_data.vix,
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as exc:
        print(f"MOVRvest market snapshot failed: {exc}")
        return 1

    MarketRenderer.render(snapshot)
    return 0