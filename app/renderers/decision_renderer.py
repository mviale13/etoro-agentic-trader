from app.domain.decision import Decision


class DecisionRenderer:
    @staticmethod
    def render(decision: Decision) -> None:
        print()
        print("MOVRvest")
        print("Invest with intelligence.")
        print()
        print("Decision")
        print("────────────────────────────────")
        print()

        print(f"Action      : {decision.action}")
        print(f"Priority    : {decision.priority}")
        print(f"Confidence  : {decision.confidence}%")

        print()
        print("Reason")
        print()

        print(decision.explanation)
        print()
