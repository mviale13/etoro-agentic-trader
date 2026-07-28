from typing import Protocol

from app.domain.brain_context import BrainContext
from app.domain.insight import Insight


class CommitteeMember(Protocol):
    def analyze(
        self,
        context: BrainContext,
    ) -> list[Insight]: ...
