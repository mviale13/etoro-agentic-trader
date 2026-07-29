from typing import Any

from app.domain.company_research_context import CompanyResearchContext
from app.domain.research_plan import ResearchPlan
from app.services.analyst_registry import AnalystRegistry


class ResearchExecutor:
    """Executes the analysts assigned by a research plan."""

    def __init__(self, registry: AnalystRegistry) -> None:
        self._registry = registry

    def execute(
        self,
        plan: ResearchPlan,
        context: CompanyResearchContext,
    ) -> list[Any]:
        opinions: list[Any] = []

        for analyst_key in plan.analyst_keys:
            analyst = self._registry.get(analyst_key)
            opinions.append(analyst.analyze(context))

        return opinions
