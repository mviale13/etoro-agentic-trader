"""Reasoning stage for the MOVRvest investment-brain pipeline."""

from app.domain.brain_context import BrainContext
from app.domain.insight import Insight
from app.services.executive_reasoning_service import ExecutiveReasoningService


class ReasoningStage:
    """Convert perceived investment context into executive insights."""

    def execute(self, context: BrainContext) -> list[Insight]:
        """Run the current executive reasoning service."""
        return ExecutiveReasoningService().analyze(context)
