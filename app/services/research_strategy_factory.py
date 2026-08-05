"""Select the research strategy a security's playbook calls for."""

from __future__ import annotations

from app.domain.company_profile import CompanyProfile
from app.domain.playbook import InvestmentPlaybook
from app.services.playbook_selector import PlaybookSelector
from app.services.research_strategy import (
    PlaybookResearchStrategy,
    ResearchStrategy,
)


class ResearchStrategyFactory:
    """
    Choose the playbook for a profile, and the strategy that runs it.

    This used to accept exactly one business model and raise for every
    other — which was safe only because the profiler could not produce
    another. Every security now reaches a playbook, including the ones
    whose playbook runs no company analysts at all.
    """

    def __init__(self, selector: PlaybookSelector | None = None) -> None:
        self._selector = selector or PlaybookSelector()

    def playbook(self, profile: CompanyProfile) -> InvestmentPlaybook:
        return self._selector.select(profile)

    def create(self, profile: CompanyProfile) -> ResearchStrategy:
        return PlaybookResearchStrategy(self.playbook(profile))
