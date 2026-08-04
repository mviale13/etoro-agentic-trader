from typing import Any

from app.domain.company_research_context import CompanyResearchContext


class CompanyFactsAnalystAdapter:
    """Adapts an existing CompanyFacts analyst to a context-aware interface."""

    def __init__(self, analyst: Any) -> None:
        self._analyst = analyst

    def analyze(self, context: CompanyResearchContext) -> Any:
        return self._analyst.analyze(context.facts)
