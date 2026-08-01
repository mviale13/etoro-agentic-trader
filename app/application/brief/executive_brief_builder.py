"""Build the Artificial CIO executive brief."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.cio.decision_state import DecisionState
from app.domain.executive.executive_brief import (
    ExecutiveBrief,
    ExecutivePriority,
)


@dataclass(slots=True)
class ExecutiveBriefBuilder:
    """Build an executive brief from a completed executive workspace."""

    #: Decision states the investor is asked to look at.
    ACTIONABLE_STATES = (
        DecisionState.RECOMMEND.value,
        DecisionState.PREPARE.value,
    )

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

    def build_portfolio(
        self,
        workspaces: Sequence[ExecutiveWorkspace],
    ) -> ExecutiveBrief:
        """
        Explain a whole portfolio in one brief.

        Workspaces are explained in the order given: the caller owns ranking.
        This builder explains decisions; it never makes or re-scores them.
        """

        if not workspaces:
            raise ValueError(
                "ExecutiveBriefBuilder requires at least one workspace.",
            )

        ranked = workspaces

        briefs = tuple(self.build(workspace) for workspace in ranked)

        actionable = tuple(
            workspace
            for workspace in ranked
            if self._decision_state(workspace) in self.ACTIONABLE_STATES
        )

        first = ranked[0]

        assert first.reasoning is not None

        return ExecutiveBrief(
            headline=self._portfolio_headline(ranked, actionable),
            summary=self._portfolio_summary(ranked, actionable),
            confidence=self._mean(
                tuple(brief.confidence for brief in briefs),
            ),
            portfolio_health=first.reasoning.portfolio.health_score,
            # Priorities are attention items. A holding the CIO is content to
            # monitor is reported in the investment cases, not asked about.
            priorities=tuple(
                priority
                for workspace, brief in zip(ranked, briefs, strict=True)
                if workspace in actionable
                for priority in brief.priorities
            ),
            investment_cases=tuple(
                case for brief in briefs for case in brief.investment_cases
            ),
        )

    @staticmethod
    def _conviction(workspace: ExecutiveWorkspace) -> int:
        return workspace.decision.conviction if workspace.decision else 0

    @staticmethod
    def _decision_state(workspace: ExecutiveWorkspace) -> str:
        return workspace.decision.state.value if workspace.decision else ""

    @staticmethod
    def _mean(values: tuple[float, ...]) -> float:
        if not values:
            return 0.0

        return sum(values) / len(values)

    @staticmethod
    def _portfolio_headline(
        ranked: Sequence[ExecutiveWorkspace],
        actionable: Sequence[ExecutiveWorkspace],
    ) -> str:
        reviewed = (
            f"{len(ranked)} position reviewed"
            if len(ranked) == 1
            else f"{len(ranked)} positions reviewed"
        )

        if not actionable:
            return f"{reviewed} · none require action"

        return f"{reviewed} · {len(actionable)} require attention"

    @staticmethod
    def _portfolio_summary(
        ranked: Sequence[ExecutiveWorkspace],
        actionable: Sequence[ExecutiveWorkspace],
    ) -> str:
        if not actionable:
            return (
                "The Artificial CIO reviewed every holding and found nothing "
                "that currently warrants action."
            )

        symbols = ", ".join(workspace.symbol for workspace in actionable)

        return (
            f"The Artificial CIO is prepared to act on {symbols}. "
            f"The remaining {len(ranked) - len(actionable)} "
            "holdings stay under monitoring."
        )
