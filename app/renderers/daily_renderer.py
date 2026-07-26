from app.domain.committee_decision import CommitteeDecision
from app.domain.market_intelligence import MarketIntelligence
from app.domain.portfolio_snapshot import PortfolioSnapshot


class DailyRenderer:
    @staticmethod
    def render(
        portfolio: PortfolioSnapshot,
        intelligence: MarketIntelligence,
        committee: CommitteeDecision,
    ) -> None:
        print()
        print("MOVRvest")
        print("Daily Brief")
        print("════════════════════════════════════")
        print()

        print("Portfolio")
        print("────────────────────────────────────")

        print(f"Portfolio Value : ${portfolio.total_value:,.2f}")
        print(f"Cash            : {portfolio.allocation.cash:.1f}%")
        print(f"Positions       : {portfolio.positions}")

        print()

        print("Market")
        print("────────────────────────────────────")

        print(f"Mood            : {intelligence.market.market_mood.title()}")
        print(f"Volatility      : {intelligence.market.volatility.title()}")
        print(
            f"Crypto Sentiment: "
            f"{intelligence.sentiment.score} "
            f"({intelligence.sentiment.label})"
        )

        print()

        print("Investment Committee")
        print("────────────────────────────────────")

        print(f"Recommendation  : {committee.recommendation}")
        print(f"Confidence      : {committee.confidence}%")

        print()

        print("Votes")

        print(f"BUY             : {committee.buy_votes}")
        print(f"HOLD            : {committee.hold_votes}")
        print(f"SELL            : {committee.sell_votes}")

        print()

        print("Committee Members")
        print("────────────────────────────────────")

        for opinion in committee.opinions:
            print(f"{opinion.member:<18}{opinion.vote:<6}{opinion.confidence:>3}%")

        print()
