"""Public Artificial CIO service."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.application.executive.executive_evaluation import (
    ExecutiveEvaluation,
)
from app.application.workspace.executive_pipeline import (
    ExecutivePipeline,
)
from app.brain import Brain
from app.domain.executive_decision import ExecutiveDecision


@dataclass(slots=True)
class ExecutiveService:
    """
    Public entry point for the Artificial CIO.

    The execution pipeline is delegated to ExecutivePipeline.
    """

    pipeline: ExecutivePipeline = field(
        default_factory=ExecutivePipeline,
    )

    def decide(
        self,
        symbol: str,
        brain: Brain,
    ) -> ExecutiveDecision:
        """
        Return only the final investment decision.
        """

        return self.evaluate(
            symbol=symbol,
            brain=brain,
        ).decision

    def evaluate(
        self,
        symbol: str,
        brain: Brain,
    ) -> ExecutiveEvaluation:
        """
        Execute the complete Artificial CIO pipeline.
        """

        return self.pipeline.evaluate(
            symbol=symbol,
            brain=brain,
        )
