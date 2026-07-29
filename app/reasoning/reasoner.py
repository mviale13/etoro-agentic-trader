from typing import Protocol

from app.brain import Brain


class Reasoner(Protocol):
    """
    Contract implemented by every cognitive reasoner.

    A reasoner receives the Brain's current understanding,
    enriches it if necessary, and returns a Brain for the
    next stage of the reasoning pipeline.
    """

    def reason(
        self,
        brain: Brain,
    ) -> Brain: ...
