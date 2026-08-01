"""
Canonical reasoning contract for the MOVRvest Artificial CIO.

The Brain bounded context exposes a single immutable cognitive model
(`Brain`). Implementations of this protocol analyze that model and
produce a `ReasoningSnapshot`.

This protocol intentionally coexists with the legacy `ReasoningEngine`
contract during the migration.

Migration roadmap:

    Legacy
    ------
    BrainContext
        ↓
    ReasoningEngine
        ↓
    list[Insight]

    Canonical
    ---------
    Brain
        ↓
    BrainReasoner
        ↓
    ReasoningSnapshot
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
