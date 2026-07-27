from app.domain.committee_decision import CommitteeDecision


class RecommendationCoach:
    def explain(
        self,
        symbol: str,
        decision: CommitteeDecision,
    ) -> str:
        recommendation = decision.recommendation

        if recommendation == "BUY":
            action = "consider buying"

        elif recommendation == "SELL":
            action = "consider reducing"

        else:
            action = "maintain your current position in"

        return (
            f"I recommend you {action} {symbol}. "
            f"The committee reached a {recommendation} decision "
            f"with {decision.confidence}% confidence."
        )
