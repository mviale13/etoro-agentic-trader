from dataclasses import dataclass

from app.brain import Brain

from .reasoner import Reasoner


@dataclass(slots=True, frozen=True)
class ReasoningPipeline:
    """
    Executes the MOVRvest cognitive reasoning pipeline.

    Each reasoner receives the current Brain and returns
    an enriched Brain for the next stage.
    """

    reasoners: tuple[Reasoner, ...]

    def run(
        self,
        brain: Brain,
    ) -> Brain:
        current = brain

        for reasoner in self.reasoners:
            current = reasoner.reason(current)

        return current
