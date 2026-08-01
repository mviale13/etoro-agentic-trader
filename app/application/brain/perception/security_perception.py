"""Per-security perception for the MOVRvest investment brain."""

from __future__ import annotations

import asyncio

from app.domain.company_recommendation import CompanyRecommendation
from app.domain.portfolio_snapshot import PortfolioSnapshot
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
    Collect evidence about each individual holding.

    Portfolio and market perception describe the whole account. This
    component describes the securities inside it, so reasoning can tell one
    holding apart from another.

    A security this component cannot describe simply produces no evidence.
    Absent evidence is reported as absent; it is never estimated.
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
    ) -> dict[str, tuple[object, ...]]:
        """Return per-symbol evidence, keyed by ticker symbol."""

        if not portfolio.holdings:
            return {}

        instruments = await self._symbol_resolver.items()

        targets = [
            (holding.symbol, instruments[holding.instrument_id])
            for holding in portfolio.holdings
            if holding.is_resolved and holding.instrument_id in instruments
        ]

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
