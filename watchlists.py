import asyncio

from app.services.watchlist_service import WatchlistService


async def main() -> None:
    watchlists = await WatchlistService().get()

    print()

    for watchlist in watchlists:
        print(f"{watchlist.name}")

        for item in watchlist.items[:10]:
            print(f"  • {item.symbol:<8} {item.name}")

        print()


asyncio.run(main())
