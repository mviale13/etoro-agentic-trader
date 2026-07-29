"""Central application orchestrator for MOVRvest investment intelligence."""

from app.domain.brain_snapshot import BrainSnapshot
from app.services.brain_context_builder import BrainContextBuilder
from app.services.executive_reasoning_service import ExecutiveReasoningService
from app.services.executive_summary_service import ExecutiveSummaryService


class InvestmentBrain:
    """Coordinate perception, reasoning, and communication for one brain cycle.

    The brain is an application-layer orchestrator. It gathers a complete
    context, delegates investment reasoning, and converts the resulting
    insights into the executive snapshot consumed by presentation layers.
    """

    async def analyze(self) -> BrainSnapshot:
        """Run one complete MOVRvest investment-intelligence cycle."""
        context = await BrainContextBuilder().build()

        insights = ExecutiveReasoningService().analyze(context)

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

    async def build(self) -> BrainSnapshot:
        """Compatibility verb for callers that still use ``build``."""
        return await self.analyze()
