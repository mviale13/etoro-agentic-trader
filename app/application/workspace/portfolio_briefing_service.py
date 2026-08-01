"""Portfolio-wide Artificial CIO briefing."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.brief.executive_brief_builder import (
    ExecutiveBriefBuilder,
)
from app.application.workspace.executive_pipeline import ExecutivePipeline
from app.application.workspace.executive_workspace import ExecutiveWorkspace
from app.brain import Brain
from app.domain.executive.executive_brief import ExecutiveBrief


@dataclass(frozen=True, slots=True)
class PortfolioBriefing:
    """A whole-portfolio briefing and the evaluations behind it."""

    brief: ExecutiveBrief

    #: Ranked by the conviction the Artificial CIO assigned, highest first.
    workspaces: tuple[ExecutiveWorkspace, ...]


@dataclass(slots=True)
class PortfolioBriefingService:
    """
    Run the Artificial CIO across every holding in the portfolio.

    The Brain is perceived once and shared by every evaluation, so each
    holding is judged against exactly the same view of reality.
    """

    pipeline: ExecutivePipeline = field(
        default_factory=ExecutivePipeline,
    )

    brief_builder: ExecutiveBriefBuilder = field(
        default_factory=ExecutiveBriefBuilder,
    )

    def symbols(
        self,
        brain: Brain,
    ) -> tuple[str, ...]:
        """Return the held symbols, in stable order and without duplicates."""

        return tuple(
            dict.fromkeys(
                holding.symbol.upper().strip()
                for holding in brain.portfolio.holdings
                if holding.symbol.strip()
            )
        )

    def evaluate(
        self,
        brain: Brain,
    ) -> tuple[ExecutiveWorkspace, ...]:
        """Evaluate every holding against the same Brain."""

        return tuple(
            self.pipeline.execute(
                symbol=symbol,
                brain=brain,
            )
            for symbol in self.symbols(brain)
        )

    def build(
        self,
        brain: Brain,
    ) -> PortfolioBriefing | None:
        """
        Explain the whole portfolio, ranked by conviction.

        Returns None when the portfolio holds nothing, because there is no
        investment reality to explain.
        """

        workspaces = self.evaluate(brain)

        if not workspaces:
            return None

        ranked = tuple(
            sorted(
                workspaces,
                key=self._conviction,
                reverse=True,
            )
        )

        return PortfolioBriefing(
            brief=self.brief_builder.build_portfolio(ranked),
            workspaces=ranked,
        )

    @staticmethod
    def _conviction(
        workspace: ExecutiveWorkspace,
    ) -> int:
        return workspace.decision.conviction if workspace.decision else 0
