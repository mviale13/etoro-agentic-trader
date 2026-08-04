from app.domain.committee_decision import CommitteeDecision


class CommitteeRenderer:
    @staticmethod
    def render(decision: CommitteeDecision) -> None:
        print()
        print("MOVRvest")
        print("Investment Committee")
        print("────────────────────────────────")
        print()

        print(f"Recommendation : {decision.recommendation}")
        print(f"Confidence     : {decision.confidence}%")
        print()

        print("Votes")
        print(f"BUY  : {decision.buy_votes}")
        print(f"HOLD : {decision.hold_votes}")
        print(f"SELL : {decision.sell_votes}")

        print()

        for opinion in decision.opinions:
            print(f"{opinion.member:<12}{opinion.vote:<6}{opinion.confidence:>3}%")

        print()
