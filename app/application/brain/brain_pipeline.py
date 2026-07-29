"""Execution pipeline for MOVRvest investment intelligence."""

from app.application.brain.communication_stage import CommunicationStage
from app.application.brain.perception_stage import PerceptionStage
from app.application.brain.reasoning_stage import ReasoningStage
from app.domain.brain_snapshot import BrainSnapshot


class BrainPipeline:
    """Execute perception, reasoning, and communication in sequence."""

    def __init__(
        self,
        perception: PerceptionStage | None = None,
        reasoning: ReasoningStage | None = None,
        communication: CommunicationStage | None = None,
    ) -> None:
        self._perception = perception or PerceptionStage()
        self._reasoning = reasoning or ReasoningStage()
        self._communication = communication or CommunicationStage()

    async def run(self) -> BrainSnapshot:
        """Run one complete MOVRvest investment-intelligence pipeline."""
        context = await self._perception.execute()
        insights = self._reasoning.execute(context)

        return self._communication.execute(
            context,
            insights,
        )
