from app.domain.market_intelligence import MarketIntelligence
from app.domain.sentiment_snapshot import NO_EQUITY_SENTIMENT


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
            print("Sentiment       : not available")
        else:
            # Named by subject. The index describes one asset class, and a
            # line that omits which one invites the reader to apply it to
            # everything they hold.
            label = f"{sentiment.subject.value.capitalize()} sentiment"

            print(f"{label:<16}: {sentiment.score} ({sentiment.label})")
            print(f"{'Source':<16}: {sentiment.reading.source}")
            print(
                f"{'Published':<16}: {sentiment.reading.observed_at.date().isoformat()}"
            )

        # Stated whether the crypto index above was read or not: the equities
        # the investor mostly holds have no sentiment index either way.
        print(NO_EQUITY_SENTIMENT)

        print()
        print(f"{'Outlook':<16}: {intelligence.outlook}")
        print(f"{'Confidence':<16}: {intelligence.confidence}%")

        print()
        print(intelligence.summary)
        print()
