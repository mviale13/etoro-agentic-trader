from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_signals import CompanySignals
from app.domain.provenance import least_reliable
from app.domain.quality_signal import QualitySignal
from app.domain.watchlist_item import WatchlistItem
from app.services.company_facts_service import CompanyFactsService
from app.services.crypto_quality_signal_service import (
    CryptoQualitySignalService,
)
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

        asset_class = AssetClass.from_etoro(item.asset_type_id)

        return CompanySignals(
            value=ValueSignalService().build(facts, asset_class),
            momentum=MomentumSignalService().build(facts),
            quality=self._quality(item, facts),
            risk=RiskSignalService().build(facts),
            reading=least_reliable(
                facts.price_reading,
                facts.fundamentals_reading,
            ),
        )

    @staticmethod
    def _quality(
        item: WatchlistItem,
        facts: CompanyFacts,
    ) -> QualitySignal:
        """
        Ask the security the questions it can answer.

        Company quality is size, earnings and dividends. A token has none
        of the three, so every crypto asset scored UNKNOWN and stopped at
        research — for an asset class this investor's policy prefers.
        """

        if AssetClass.from_etoro(item.asset_type_id) is AssetClass.CRYPTO:
            return CryptoQualitySignalService().build(facts)

        return QualitySignalService().build(facts)
