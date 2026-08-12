from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.company_facts import CompanyFacts
from app.domain.company_research import CompanyResearch
from app.domain.company_signals import CompanySignals
from app.domain.provenance import least_reliable
from app.domain.quality_signal import QualitySignal
from app.domain.watchlist_item import WatchlistItem
from app.services.company_facts_service import CompanyFactsService
from app.services.company_research_service import CompanyResearchService
from app.services.crypto_asset_quality_service import (
    CryptoAssetQualityService,
    signal_of,
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
            research=await self._research(asset_class, facts),
            # Carried, not judged: the investment case reads a security
            # through its signals, and this is the only object that
            # reaches it.
            earnings=facts.earnings,
            reading=least_reliable(
                facts.price_reading,
                facts.fundamentals_reading,
            ),
        )

    @staticmethod
    async def _research(
        asset_class: AssetClass,
        facts: CompanyFacts,
    ) -> CompanyResearch | None:
        """
        The security read the way its own playbook says it should be.

        Every security gets one, including the ones no company analyst is
        asked about. This used to return nothing at all for a fund or a
        token — correct in that neither has margins, and silent about why,
        so their dossiers simply had less on them than a company's with no
        explanation for the difference. The playbook is that explanation,
        and a security whose playbook runs no analysts now carries it.

        The analysts already handle a figure they cannot read as an
        unknown, so a company whose fundamentals did not come back gets a
        research package that says so rather than none at all.
        """

        return await CompanyResearchService().analyze(facts)

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

        A token is now asked the questions its *archetype* is asked, and
        answered only where the evidence stands up. It reads the crypto
        evidence families directly rather than through `CompanyFacts`:
        the generic `circulating_supply` field is not a crypto concept
        and the supply work proved a number without its concept cannot
        be compared with anything. `facts` is still the equity route and
        is untouched.
        """

        asset_class = AssetClass.from_etoro(item.asset_type_id)

        if asset_class is AssetClass.CRYPTO:
            quality = CryptoAssetQualityService().established(
                item.symbol,
                asset_class,
            )

            if quality is not None:
                return signal_of(quality)

        # The asset class travels with the question, so an asset with no
        # company behind it — a fund included — is told apart from a
        # company whose figures did not come back. Without it, whichever
        # single field the provider happened to answer became the whole
        # quality story.
        return QualitySignalService().build(facts, asset_class)
