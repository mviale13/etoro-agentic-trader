"""Central application entry point for MOVRvest investment intelligence."""

from app.application.brain.brain_pipeline import BrainPipeline
from app.domain.brain_snapshot import BrainSnapshot


class InvestmentBrain:
    """Expose the MOVRvest investment brain to presentation-layer callers.

    Execution details belong to ``BrainPipeline``. This class remains the
    stable application entry point consumed by APIs and other presentation
    adapters.
    """

    def __init__(self, pipeline: BrainPipeline | None = None) -> None:
        self._pipeline = pipeline or BrainPipeline()

    async def analyze(self) -> BrainSnapshot:
        """Run one complete MOVRvest investment-intelligence cycle."""
        return await self._pipeline.run()

    async def build(self) -> BrainSnapshot:
        """Compatibility verb for callers that still use ``build``."""
        return await self.analyze()
