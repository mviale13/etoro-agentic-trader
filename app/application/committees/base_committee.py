"""Base Executive Committee."""

from __future__ import annotations

from typing import Protocol

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.application.committees.models.committee_opinion import (
    CommitteeOpinion,
)
from app.brain import Brain


class ExecutiveCommittee(Protocol):
    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
    ) -> CommitteeOpinion: ...
