from app.domain.brain_snapshot import BrainSnapshot
from app.services.brain_context_builder import BrainContextBuilder
from app.services.executive_reasoning_service import (
    ExecutiveReasoningService,
)
from app.services.executive_summary_service import (
    ExecutiveSummaryService,
)


class BrainService:
    async def build(self) -> BrainSnapshot:
        context = await BrainContextBuilder().build()

        insights = ExecutiveReasoningService().analyze(
            context,
        )

        communication_service = ExecutiveSummaryService()

        brief = communication_service.build(insights)
        summary = communication_service.summarize(insights)

        has_opportunity = any(
            insight.category.lower() == "opportunity" for insight in insights
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
            insights=insights,
            focus=executive_focus,
            brief=brief,
        )
