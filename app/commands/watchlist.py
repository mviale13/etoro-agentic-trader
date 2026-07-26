from app.renderers.watchlist_renderer import WatchlistRenderer
from app.services.watchlist_service import WatchlistService


async def run() -> int:
    recommendations = await WatchlistService().build()

    WatchlistRenderer.render(recommendations)

    return 0
