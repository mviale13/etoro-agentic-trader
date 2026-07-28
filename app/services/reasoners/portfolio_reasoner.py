from app.domain.brain_context import BrainContext
from app.domain.insight import Insight


class PortfolioReasoner:
    def analyze(
        self,
        context: BrainContext,
    ) -> list[Insight]:
        insights: list[Insight] = []

        investment_policy = context.investment_policy

        if investment_policy is None:
            insights.append(
                Insight(
                    priority=100,
                    category="policy",
                    title="Investment Policy not configured",
                    message=(
                        "MOVRvest cannot yet evaluate your portfolio "
                        "against personal allocation targets."
                    ),
                    evidence=[
                        "Investment strategy status: draft",
                    ],
                    recommended_action=(
                        "Complete your Investment Policy to enable "
                        "personalized portfolio reasoning."
                    ),
                    confidence="high",
                    policy_alignment=None,
                    attention_level="important",
                )
            )

            return insights

        current_cash = context.portfolio.allocation.cash
        target_cash = investment_policy.target.cash
        cash_difference = current_cash - target_cash

        if cash_difference > 5:
            insights.append(
                Insight(
                    priority=100,
                    category="opportunity",
                    title="Capital available for deployment",
                    message=(
                        "Your cash allocation is meaningfully above "
                        "your Investment Policy target."
                    ),
                    evidence=[
                        (f"Current cash allocation: {current_cash:.1f}%"),
                        (f"Investment Policy target: {target_cash:.1f}%"),
                        (
                            "Available allocation difference: "
                            f"{cash_difference:.1f} percentage points"
                        ),
                    ],
                    recommended_action=(
                        "Review the highest-ranked policy-aligned opportunities."
                    ),
                    confidence="high",
                    policy_alignment=True,
                    attention_level="important",
                )
            )

        return insights
