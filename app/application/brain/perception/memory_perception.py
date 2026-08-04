"""Memory perception component for the MOVRvest investment brain."""

from __future__ import annotations

from app.application.learning.decision_journal import DecisionJournal
from app.domain.decision_history import DecisionHistory
from app.repositories.event_repository import EventRepository


class MemoryPerception:
    """
    Perceive what the Artificial CIO decided in previous cycles.

    Perception reads reality and reports it as fact. Recorded decisions are
    that reality here: this component never re-decides, and it never fills a
    symbol that has no record with an assumed one.
    """

    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._journal = DecisionJournal(repository)

    def execute(self) -> dict[str, DecisionHistory]:
        """Return the recorded decision history, keyed by symbol."""

        return self._journal.histories()
