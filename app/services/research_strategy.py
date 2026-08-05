"""Turn a playbook into the plan the analysts are actually run from."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.playbook import InvestmentPlaybook
from app.domain.research_plan import ResearchPlan


class ResearchStrategy(ABC):
    """Defines the research required for a particular kind of company."""

    @abstractmethod
    def create_plan(self) -> ResearchPlan:
        """Create the research plan represented by this strategy."""


class PlaybookResearchStrategy(ResearchStrategy):
    """
    The plan a playbook asks for, built from the playbook itself.

    The playbook is the explanation shown to the investor; this is the
    instruction handed to the executor. Deriving one from the other is
    what stops them disagreeing — a dossier saying a bank is read without
    a cash-flow analyst, while the executor runs one anyway, would be the
    platform describing an analysis it did not perform.
    """

    def __init__(self, playbook: InvestmentPlaybook) -> None:
        self._playbook = playbook

    def create_plan(self) -> ResearchPlan:
        return ResearchPlan(
            objective=self._playbook.explanation,
            questions=self._playbook.priorities,
            analyst_keys=self._playbook.analysts,
        )
