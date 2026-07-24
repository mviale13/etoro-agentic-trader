from app.domain.decision import Decision
from app.domain.market_snapshot import MarketSnapshot
from app.domain.policy_analysis import PolicyAnalysis


class DecisionEngine:
    def evaluate(
        self,
        analysis: PolicyAnalysis,
        market: MarketSnapshot,
    ) -> Decision:

        if not analysis.compliant:
            return Decision(
                action="REBALANCE",
                priority="HIGH",
                confidence=100,
                explanation=("Your portfolio is outside your investment policy."),
            )

        if market.market_mood == "negative":
            return Decision(
                action="WAIT",
                priority="MEDIUM",
                confidence=90,
                explanation=("Markets are currently weak. Waiting is recommended."),
            )

        return Decision(
            action="HOLD",
            priority="LOW",
            confidence=85,
            explanation=("Your portfolio is aligned with your policy."),
        )
