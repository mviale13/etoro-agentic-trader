"""
Canonical reasoning contract for the MOVRvest Artificial CIO.

The Brain bounded context exposes a single immutable cognitive model
(`Brain`). Implementations of this protocol analyse that model and produce
a `ReasoningSnapshot`:

    Brain -> BrainReasoner -> ReasoningSnapshot

The legacy `BrainContext` this once coexisted with is gone; every analyst
now reasons over a `Brain` and nothing else.
"""

from typing import Protocol

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.brain.brain import Brain


class BrainReasoner(Protocol):
    """
    Canonical reasoning interface.

    Implementations perform analytical reasoning over a fully assembled
    Brain and return an immutable ReasoningSnapshot.

    Implementations should:
      - Be deterministic.
      - Never mutate the Brain.
      - Never fetch external data.
      - Never make investment decisions.
      - Never communicate with the UI.
    """

    def reason(self, brain: Brain) -> ReasoningSnapshot:
        """
        Analyze the Brain and produce a ReasoningSnapshot.
        """
        ...
