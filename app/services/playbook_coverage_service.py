"""Measure the grounded selector over the book, acquiring nothing.

The read-only measurement behind `movrvest playbook-coverage`. For every
security the investor holds or watches it consults the knowledge store
**as it stands** — never `CompanyKnowledgeService.knowledge()`, which
acquires on a cache miss — derives the understanding and the grounded
selection with the same pure functions the selector uses, and charges
every company the grounded route cannot serve with exactly one blocker.

The industry route is consulted only where the grounded route does not
serve, exactly as the migration seam consults it, and a provider that
errors while it is consulted becomes a note on the row rather than a
silent outcome: an absence in the measurement carries its reason like
any other absence on this platform.
"""

from __future__ import annotations

from typing import Any

from app.brokers.etoro_account import EtoroAccountBroker
from app.config import Settings
from app.domain.asset_class import AssetClass
from app.domain.business_understanding import BusinessUnderstanding
from app.domain.knowledge_consensus import QUORUM, consensus_of
from app.domain.playbook import PlaybookKind
from app.domain.playbook_coverage import (
    Blocker,
    CoverageOrigin,
    CoverageOutcome,
    CoverageReport,
    SecurityCoverage,
)
from app.domain.playbook_selection import PlaybookSelection
from app.domain.watchlist_item import WatchlistItem
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore
from app.services.account_service import AccountService
from app.services.company_facts_service import CompanyFactsService
from app.services.company_profiler import CompanyProfiler
from app.services.playbook_mapping import select_grounded
from app.services.playbook_selector import PlaybookSelector
from app.services.understanding_engine import understand
from app.services.watchlist_service import WatchlistService

#: Asset classes that publish no annual report a segment could be read
#: from — a token, a commodity, and a fund whose accounts describe the
#: wrapper. For these the grounded route does not apply, which is a
#: different fact from a company whose filing has not been read.
_FILES_NOTHING = (AssetClass.CRYPTO, AssetClass.COMMODITY, AssetClass.ETF)


class PlaybookCoverageService:
    def __init__(
        self,
        *,
        store: Any | None = None,
        watchlist: Any | None = None,
        account: Any | None = None,
        facts: Any | None = None,
        profiler: CompanyProfiler | None = None,
        industry: PlaybookSelector | None = None,
    ) -> None:
        self._store = store or JsonCompanyKnowledgeStore()
        self._watchlist = watchlist or WatchlistService()
        self._account = account or AccountService(EtoroAccountBroker(Settings()))
        self._facts = facts or CompanyFactsService()
        self._profiler = profiler or CompanyProfiler()
        self._industry = industry or PlaybookSelector()

    async def report(self) -> CoverageReport:
        """The measured population: every held or watched security once."""

        items: dict[str, WatchlistItem] = {}

        for watchlist in await self._watchlist.get():
            for item in watchlist.items:
                items.setdefault(item.symbol.upper(), item)

        snapshot = await self._account.snapshot()

        held: dict[str, str | None] = {
            position.symbol.upper(): position.asset_class
            for position in snapshot.positions
            if position.is_resolved
        }

        securities = []

        for symbol in sorted(set(items) | set(held)):
            origin = (
                CoverageOrigin.BOTH
                if symbol in items and symbol in held
                else CoverageOrigin.PORTFOLIO
                if symbol in held
                else CoverageOrigin.WATCHLIST
            )

            securities.append(
                await self._measure(
                    symbol,
                    origin,
                    items.get(symbol),
                    held.get(symbol),
                )
            )

        return CoverageReport(securities=tuple(securities))

    async def _measure(
        self,
        symbol: str,
        origin: CoverageOrigin,
        item: WatchlistItem | None,
        held_class: str | None,
    ) -> SecurityCoverage:
        observations = self._store.latest(symbol)

        if not observations:
            blocker, claim = self._never_read(item, held_class)
            outcome, playbook, note = await self._industry_serves(item)

            return SecurityCoverage(
                symbol=symbol,
                origin=origin,
                width=0,
                quorate=False,
                understanding=False,
                outcome=outcome,
                playbook=playbook,
                blocker=blocker,
                blocking_claim=claim,
                note=note,
            )

        understanding = understand(consensus_of(observations))
        grounded = select_grounded(understanding)

        if isinstance(grounded, PlaybookSelection):
            return SecurityCoverage(
                symbol=symbol,
                origin=origin,
                width=understanding.observation_count,
                quorate=understanding.quorate,
                understanding=True,
                outcome=CoverageOutcome.GROUNDED,
                playbook=grounded.playbook.kind,
                blocker=None,
                blocking_claim=None,
            )

        blocker, claim = self._refused(understanding)
        outcome, playbook, note = await self._industry_serves(item)

        return SecurityCoverage(
            symbol=symbol,
            origin=origin,
            width=understanding.observation_count,
            quorate=understanding.quorate,
            understanding=True,
            outcome=outcome,
            playbook=playbook,
            blocker=blocker,
            blocking_claim=claim,
            note=note,
        )

    def _never_read(
        self,
        item: WatchlistItem | None,
        held_class: str | None,
    ) -> tuple[Blocker, str]:
        """Why a store-empty security has no grounded route.

        A digital asset or a fund files nothing, so nothing could ever
        be read for it — a different fact from an equity whose filing
        simply has not been read yet, and the two must not share a
        blocker.
        """

        asset_class: AssetClass | None = None

        if item is not None:
            asset_class = AssetClass.from_etoro(item.asset_type_id)
        elif held_class is not None:
            try:
                asset_class = AssetClass(held_class)
            except ValueError:
                asset_class = None

        if asset_class in _FILES_NOTHING:
            return (
                Blocker.NO_PRIMARY_SOURCE,
                f"a {asset_class.noun} publishes no annual report to read",
            )

        return (
            Blocker.NOT_READ,
            "one observation of its current filing",
        )

    def _refused(
        self,
        understanding: BusinessUnderstanding,
    ) -> tuple[Blocker, str]:
        """The one claim in the way, decided from the understanding's
        own fields — the same facts the archetype rules refused on,
        never a parse of their wording."""

        archetype = understanding.characteristics

        if not understanding.quorate:
            missing = QUORUM - understanding.observation_count

            return (
                Blocker.BELOW_QUORUM,
                f"{missing} more observation(s) of the current filing",
            )

        if archetype.primary is not None:
            return (
                Blocker.NO_MAPPING,
                f"a playbook rule for {archetype.stated!r}, which no quorate "
                "case has earned yet",
            )

        if understanding.segments_because is not None:
            return (
                Blocker.SEGMENTS_UNSETTLED,
                "observations that agree which segments the filing names",
            )

        if archetype.candidates:
            unmeasured = next(
                (sold.name for sold in understanding.sells if sold.share is None),
                None,
            )

            return (
                Blocker.NO_SEGMENT_SIZES,
                f"a size for {unmeasured!r} proven against a table"
                if unmeasured is not None
                else "one segment size proven against a table",
            )

        if archetype.explained == 0.0:
            return (
                Blocker.NO_REVENUE_MECHANISMS,
                self._largest_unexplained(understanding),
            )

        return (
            Blocker.TOO_LITTLE_EXPLAINED,
            f"ways of earning for segments worth {0.5 - archetype.explained:.0%} "
            "more of measured revenue",
        )

    @staticmethod
    def _largest_unexplained(understanding: BusinessUnderstanding) -> str:
        """The single cheapest unlocking claim: the biggest segment whose
        way of earning is not established."""

        unexplained = [sold for sold in understanding.sells if not sold.mechanisms]

        if not unexplained:
            return "one segment's way of earning established"

        largest = max(unexplained, key=lambda sold: sold.share or 0.0)

        sized = (
            f" ({largest.share:.0%} of revenue)" if largest.share is not None else ""
        )

        return f"a way of earning established for {largest.name!r}{sized}"

    async def _industry_serves(
        self,
        item: WatchlistItem | None,
    ) -> tuple[CoverageOutcome, PlaybookKind, str | None]:
        """What the pre-existing route serves, consulted as the seam
        consults it — and only because the grounded route did not."""

        if item is None:
            return (
                CoverageOutcome.UNCLASSIFIED,
                PlaybookKind.UNCLASSIFIED,
                "no watchlist item, so no provider profile could be built",
            )

        try:
            profile = self._profiler.profile(await self._facts.build(item))
        except Exception as failure:  # noqa: BLE001 — the note carries it
            return (
                CoverageOutcome.UNCLASSIFIED,
                PlaybookKind.UNCLASSIFIED,
                f"the industry route could not be consulted: {failure}",
            )

        kind = self._industry.select(profile).kind

        if kind is PlaybookKind.UNCLASSIFIED:
            return (CoverageOutcome.UNCLASSIFIED, kind, None)

        return (CoverageOutcome.FALLBACK, kind, None)
