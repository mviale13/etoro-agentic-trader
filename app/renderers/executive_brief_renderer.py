"""Render ExecutiveBrief objects into dashboard view models."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.executive.executive_brief import (
    ExecutiveBrief,
)
from app.renderers.dashboard_view_model import (
    DashboardInvestmentCase,
    DashboardPriority,
    DashboardViewModel,
)


@dataclass(slots=True)
class ExecutiveBriefRenderer:
    """
    Converts domain objects into presentation models.

    React should consume DashboardViewModel,
    never ExecutiveBrief directly.
    """

    def render(
        self,
        brief: ExecutiveBrief,
    ) -> DashboardViewModel:

        priorities = tuple(
            DashboardPriority(
                title=p.title,
                description=p.description,
                urgency=p.urgency,
            )
            for p in brief.priorities
        )

        cases = tuple(
            DashboardInvestmentCase(
                symbol=case.symbol,
                recommendation=case.recommendation,
                confidence=case.confidence,
                conviction=case.conviction,
                summary=case.summary,
                trend=case.trend.stated if case.trend is not None else None,
            )
            for case in brief.investment_cases
        )

        return DashboardViewModel(
            headline=brief.headline,
            summary=brief.summary,
            confidence=brief.confidence,
            portfolio_health=brief.portfolio_health,
            priorities=priorities,
            investment_cases=cases,
        )
