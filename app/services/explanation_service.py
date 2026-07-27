from app.domain.explanation import Explanation


class ExplanationService:
    def build(self) -> Explanation:
        return Explanation(
            recommendation="BUY SPY",
            confidence=87,
            reasons=(
                "Momentum improved.",
                "Market risk remains moderate.",
                "Cash allocation is above target.",
            ),
        )
