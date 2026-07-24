from app.domain.market_snapshot import MarketSnapshot


class MarketRenderer:
    @staticmethod
    def render(snapshot: MarketSnapshot) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print("Market Snapshot")
        print("────────────────────────────────")
        print()

        for quote in snapshot.quotes:
            arrow = "▲" if quote.change_percent >= 0 else "▼"

            print(
                f"{quote.symbol:<6}"
                f"${quote.price:>10,.2f}   "
                f"{arrow} {quote.change_percent:+.2f}%"
            )

        print()
        print(f"Market Mood : {snapshot.market_mood.title()}")
        print(f"Volatility  : {snapshot.volatility.title()}")
        print()
        print(snapshot.summary)
        print()