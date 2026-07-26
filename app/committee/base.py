from abc import ABC, abstractmethod

from app.domain.committee_context import CommitteeContext
from app.domain.committee_opinion import CommitteeOpinion


class CommitteeMember(ABC):
    @abstractmethod
    def evaluate(
        self,
        context: CommitteeContext,
    ) -> CommitteeOpinion: ...
