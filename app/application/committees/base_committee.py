"""Base Executive Committee."""

from __future__ import annotations

from typing import Protocol

from app.application.brain.reasoning.reasoning_snapshot import (
    ReasoningSnapshot,
)
from app.brain import Brain
from app.domain.committee.opinion import (
    CommitteeOpinion,
)


class ExecutiveCommittee(Protocol):
    def review(
        self,
        brain: Brain,
        reasoning: ReasoningSnapshot,
    ) -> CommitteeOpinion: ...
