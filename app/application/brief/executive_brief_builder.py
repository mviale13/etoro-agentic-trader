"""Build the Artificial CIO executive brief."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.domain.executive.executive_brief import (
    ExecutiveBrief,
    ExecutivePriority,
)


@dataclass(slots=True)
class ExecutiveBriefBuilder:
    """Build an executive brief from a completed executive workspace."""

    def build(
        self,
        workspace: ExecutiveWorkspace,
    ) -> ExecutiveBrief:
        reasoning = workspace.reasoning
        thesis = workspace.thesis

        if reasoning is None:
            raise ValueError("ExecutiveBriefBuilder requires workspace.reasoning.")

        if thesis is None:
            raise ValueError("ExecutiveBriefBuilder requires workspace.thesis.")

        priority = ExecutivePriority(
            title=thesis.symbol,
            description=thesis.summary,
            urgency=1.0 - thesis.confidence,
        )

        return ExecutiveBrief(
            headline=(f"{thesis.symbol}: {thesis.recommendation.upper()}"),
            summary=thesis.summary,
            confidence=thesis.confidence,
            portfolio_health=reasoning.portfolio.health_score,
            priorities=(priority,),
            investment_cases=(thesis,),
        )
