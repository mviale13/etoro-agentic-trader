from app.domain.committee_decision import CommitteeDecision
from app.domain.market_intelligence import MarketIntelligence
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.sentiment_snapshot import NO_EQUITY_SENTIMENT


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
        cash = portfolio.allocation.cash
        print(
            "Cash            : " + ("unavailable" if cash is None else f"{cash:.1f}%")
        )
        print(f"Positions       : {portfolio.positions}")

        print()

        print("Market")
        print("────────────────────────────────────")

        print(f"Mood            : {intelligence.market.market_mood.title()}")
        print(f"Volatility      : {intelligence.market.volatility.title()}")
        sentiment = intelligence.sentiment

        print(
            "Crypto Sentiment: "
            + (
                "not available"
                if sentiment is None
                else f"{sentiment.score} ({sentiment.label})"
            )
        )
        print(NO_EQUITY_SENTIMENT)

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
            if not opinion.participates:
                print(f"{opinion.member:<18}{'ABSTAIN':<6}  —")
                continue

            print(f"{opinion.member:<18}{opinion.vote:<6}{opinion.confidence:>3}%")

        print()
