"""Per-security perception for the MOVRvest investment brain."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

from app.domain.company_recommendation import CompanyRecommendation
from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.research_candidate import ResearchCandidate
from app.domain.watchlist_item import WatchlistItem
from app.services.company_committee_service import (
    CompanyCommitteeService,
)
from app.services.company_signal_service import CompanySignalService
from app.services.instrument_symbol_resolver import (
    InstrumentSymbolResolver,
)


class SecurityPerception:
    """
    Collect evidence about each individual security.

    Portfolio and market perception describe the whole account. This
    component describes the securities the Artificial CIO may judge — every
    holding, and the research candidates it is asked to look at — so
    reasoning can tell one investment case apart from another.

    A security this component cannot describe simply produces no evidence.
    Absent evidence is reported as absent; it is never estimated.

    Candidates are evidenced up to a limit the caller sets. Each one costs a
    fundamentals request, and the provider rate-limits, so the caller decides
    how much of the universe a single cycle can honestly cover.
    """

    def __init__(
        self,
        symbol_resolver: InstrumentSymbolResolver | None = None,
        signal_service: CompanySignalService | None = None,
        committee_service: CompanyCommitteeService | None = None,
    ) -> None:
        self._symbol_resolver = symbol_resolver or InstrumentSymbolResolver()
        self._signal_service = signal_service or CompanySignalService()
        self._committee_service = committee_service or CompanyCommitteeService()

    async def execute(
        self,
        portfolio: PortfolioSnapshot,
        candidates: Sequence[ResearchCandidate] = (),
        candidate_limit: int = 0,
    ) -> dict[str, tuple[object, ...]]:
        """Return per-symbol evidence, keyed by ticker symbol."""

        if not portfolio.holdings and not candidates:
            return {}

        instruments = await self._symbol_resolver.items()

        targets = [
            (holding.symbol, instruments[holding.instrument_id])
            for holding in portfolio.holdings
            if holding.is_resolved and holding.instrument_id in instruments
        ]

        targets.extend(
            self._candidate_targets(
                candidates,
                instruments,
                candidate_limit,
            )
        )

        if not targets:
            return {}

        recommendations = await asyncio.gather(
            *(self._evaluate(symbol, item) for symbol, item in targets),
            return_exceptions=True,
        )

        evidence: dict[str, tuple[object, ...]] = {}

        for (symbol, _), recommendation in zip(
            targets,
            recommendations,
            strict=True,
        ):
            if isinstance(recommendation, CompanyRecommendation):
                evidence[symbol] = (recommendation,)

        return evidence

    @staticmethod
    def _candidate_targets(
        candidates: Sequence[ResearchCandidate],
        instruments: dict[int, WatchlistItem],
        limit: int,
    ) -> list[tuple[str, WatchlistItem]]:
        """Choose the candidates this cycle can afford to evidence."""

        if limit <= 0:
            return []

        targets: list[tuple[str, WatchlistItem]] = []

        for candidate in candidates:
            if len(targets) >= limit:
                break

            item = instruments.get(candidate.instrument_id)

            if item is not None:
                targets.append((candidate.symbol, item))

        return targets

    async def _evaluate(
        self,
        symbol: str,
        item: WatchlistItem,
    ) -> CompanyRecommendation:
        signals = await self._signal_service.build(item)

        return self._committee_service.evaluate(
            symbol,
            signals,
        )
