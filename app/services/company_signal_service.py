from typing import Protocol

from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.watchlist_item import WatchlistItem
from app.services.company_facts_service import CompanyFactsService
from app.services.momentum_signal_service import MomentumSignalService
from app.services.quality_signal_service import QualitySignalService
from app.services.risk_signal_service import RiskSignalService
from app.services.value_signal_service import ValueSignalService


class CompanyFactsProvider(Protocol):
    async def build(
        self,
        item: WatchlistItem,
    ) -> CompanyFacts: ...


class CompanySignalService:
    def __init__(
        self,
        facts_service: CompanyFactsProvider | None = None,
    ) -> None:
        self._facts = facts_service or CompanyFactsService()

    async def build(
        self,
        item: WatchlistItem,
    ) -> CompanySignals:
        facts = await self._facts.build(item)

        return CompanySignals(
            value=ValueSignalService().build(facts),
            momentum=MomentumSignalService().build(facts),
            quality=QualitySignalService().build(facts),
            risk=RiskSignalService().build(facts),
        )
