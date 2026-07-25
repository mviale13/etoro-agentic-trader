from app.domain.market_intelligence import MarketIntelligence


class IntelligenceRenderer:
    @staticmethod
    def render(intelligence: MarketIntelligence) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print("MARKET INTELLIGENCE")
        print("────────────────────────────────")
        print()

        print(f"Market mood     : {intelligence.market.market_mood.title()}")
        print(f"Volatility      : {intelligence.market.volatility.title()}")

        print()
        print(
            f"Crypto sentiment: "
            f"{intelligence.sentiment.score} "
            f"({intelligence.sentiment.label})"
        )
        print(f"Source           : {intelligence.sentiment.source}")

        print()
        print(f"Outlook          : {intelligence.outlook}")
        print(f"Confidence       : {intelligence.confidence}%")

        print()
        print(intelligence.summary)
        print()
