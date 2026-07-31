"""Legacy compatibility adapter for the reasoning pipeline."""

from app.domain.brain_context import BrainContext
from app.domain.insight import Insight
from app.services.executive_committee_service import (
    ExecutiveCommitteeService,
)


class ExecutiveReasoningService:
    """
    Compatibility adapter.

    Preserves the legacy `analyze()` API while the canonical Brain pipeline
    is migrated.

    Canonical reasoning now runs through:

        BrainBuilderService
            ↓
        Brain
            ↓
        ExecutivePipeline
            ↓
        ExecutiveBrief

    This adapter only preserves the existing committee behaviour until the
    legacy Insight pipeline is replaced by that brief.
    """

    def analyze(
        self,
        context: BrainContext,
    ) -> list[Insight]:
        # Preserve the existing committee behaviour for now.
        ExecutiveCommitteeService().vote(context)

        # TODO: Replace the legacy Insight pipeline with the ExecutiveBrief
        # produced by ExecutivePipeline.
        return []
