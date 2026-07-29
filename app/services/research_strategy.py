from abc import ABC, abstractmethod

from app.domain.research_plan import AnalystKey, ResearchPlan


class ResearchStrategy(ABC):
    """Defines the research required for a particular kind of company."""

    @abstractmethod
    def create_plan(self) -> ResearchPlan:
        """Create the research plan represented by this strategy."""


class CorporateResearchStrategy(ResearchStrategy):
    """Research strategy for a standard corporate business."""

    def create_plan(self) -> ResearchPlan:
        return ResearchPlan(
            objective="Evaluate long-term investment attractiveness.",
            questions=(
                "Can earnings continue growing?",
                "Is the company consistently profitable?",
                "Is the balance sheet resilient?",
                "Does the company generate durable cash flow?",
            ),
            analyst_keys=(
                AnalystKey.GROWTH,
                AnalystKey.PROFITABILITY,
                AnalystKey.BALANCE_SHEET,
                AnalystKey.CASH_FLOW,
            ),
        )
