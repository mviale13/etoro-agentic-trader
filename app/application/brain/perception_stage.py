"""Perception stage for the MOVRvest investment-brain pipeline."""

from app.domain.brain_context import BrainContext
from app.services.brain_context_builder import BrainContextBuilder


class PerceptionStage:
    """Gather the complete context required for one brain cycle."""

    async def execute(self) -> BrainContext:
        """Build and return the current investment context."""
        return await BrainContextBuilder().build()
