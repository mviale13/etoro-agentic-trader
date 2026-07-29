"""Communication stage for the MOVRvest investment-brain pipeline."""

from collections.abc import Sequence

from app.domain.brain_context import BrainContext
from app.domain.brain_snapshot import BrainSnapshot
from app.domain.insight import Insight
from app.services.executive_summary_service import ExecutiveSummaryService


class CommunicationStage:
    """Convert investment reasoning into a presentation-ready brain snapshot."""

    def execute(
        self,
        context: BrainContext,
        insights: Sequence[Insight],
    ) -> BrainSnapshot:
        """Build the executive communication output for one brain cycle."""
        communication_service = ExecutiveSummaryService()

        insight_list = list(insights)
        brief = communication_service.build(insight_list)
        summary = communication_service.summarize(insight_list)

        has_opportunity = any(
            insight.category.lower() == "opportunity" for insight in insight_list
        )

        has_deployable_cash = False

        if context.investment_policy is not None:
            policy_cash_target = context.investment_policy.target.cash
            current_cash = context.portfolio.allocation.cash
            has_deployable_cash = current_cash > policy_cash_target + 5

        executive_focus = (
            "opportunities" if has_deployable_cash and has_opportunity else "portfolio"
        )

        return BrainSnapshot(
            portfolio=context.portfolio,
            recommendation=context.recommendation,
            observation=context.observation,
            investor_dna=context.investor_dna,
            summary=summary,
            insights=insight_list,
            focus=executive_focus,
            brief=brief,
        )
