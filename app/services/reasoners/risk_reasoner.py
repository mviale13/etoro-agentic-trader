from app.domain.brain_context import BrainContext
from app.domain.insight import Insight


class RiskReasoner:
    def analyze(
        self,
        context: BrainContext,
    ) -> list[Insight]:
        insights: list[Insight] = []

        if context.portfolio.allocation.cash < 10:
            insights.append(
                Insight(
                    priority=95,
                    category="risk",
                    title="Low Cash Buffer",
                    message=(
                        "Cash reserves are low. "
                        "Consider preserving liquidity "
                        "for future opportunities."
                    ),
                    evidence=[
                        (f"Cash allocation: {context.portfolio.allocation.cash:.1f}%"),
                    ],
                )
            )

        return insights
