from app.renderers.watchlist_renderer import WatchlistRenderer
from app.services.watchlist_service import WatchlistService


async def run() -> int:
    results = WatchlistService().build()

    WatchlistRenderer.render(results)

    return 0
