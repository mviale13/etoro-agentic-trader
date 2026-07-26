from app.domain.watchlist_result import WatchlistResult


class WatchlistService:
    def build(self) -> list[WatchlistResult]:
        return [
            WatchlistResult("ASML", "BUY", 91),
            WatchlistResult("MSFT", "BUY", 88),
            WatchlistResult("GOOGL", "BUY", 84),
            WatchlistResult("META", "HOLD", 74),
            WatchlistResult("AMD", "SELL", 58),
        ]
