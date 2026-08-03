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

        # The source line is a citation. It is printed only beside a figure
        # actually read from that source — the pair used to appear over a
        # hardcoded number, which is what made it convincing.
        sentiment = intelligence.sentiment

        if sentiment is None:
            print("Crypto sentiment: not available")
        else:
            print(f"Crypto sentiment: {sentiment.score} ({sentiment.label})")
            print(f"Source           : {sentiment.source}")

            if sentiment.observed_at is not None:
                print(f"Published        : {sentiment.observed_at.date().isoformat()}")

        print()
        print(f"Outlook          : {intelligence.outlook}")
        print(f"Confidence       : {intelligence.confidence}%")

        print()
        print(intelligence.summary)
        print()
