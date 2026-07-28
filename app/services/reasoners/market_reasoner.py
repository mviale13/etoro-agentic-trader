from app.domain.brain_context import BrainContext
from app.domain.insight import Insight


class MarketReasoner:
    def analyze(
        self,
        context: BrainContext,
    ) -> list[Insight]:
        insights: list[Insight] = []

        if context.market.regime == "Bullish":
            insights.append(
                Insight(
                    priority=90,
                    category="market",
                    title="Bullish market conditions",
                    message=("The market remains supportive for long-term investing."),
                    evidence=[
                        (f"Market regime: {context.market.regime}"),
                    ],
                    recommended_action=(
                        "Continue evaluating policy-aligned opportunities."
                    ),
                    confidence="medium",
                    policy_alignment=None,
                    attention_level="informational",
                )
            )

        return insights
