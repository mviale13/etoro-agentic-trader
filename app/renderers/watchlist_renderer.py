from app.domain.watchlist_result import WatchlistResult


class WatchlistRenderer:
    @staticmethod
    def render(results: list[WatchlistResult]) -> None:
        print()
        print("MOVRvest")
        print("Watchlist")
        print("══════════════════════════════")
        print()

        for result in results:
            print(f"{result.symbol:<8}{result.recommendation:<6}{result.confidence}%")
