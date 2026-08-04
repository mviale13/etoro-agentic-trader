"""Per-security perception for the MOVRvest investment brain."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field

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


@dataclass(frozen=True, slots=True)
class SecurityEvidence:
    """
    What one perception cycle looked at, and what it could describe.

    `attempted_candidates` records which candidates the cycle actually
    spent a fundamentals request on. Without that record, "reviewed" had
    to be reconstructed downstream by arithmetic on the budget — a claim
    about what happened, made by someone who was not there.
    """

    evidence: dict[str, tuple[object, ...]] = field(default_factory=dict)
    attempted_candidates: tuple[str, ...] = ()


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
        focus_symbols: Sequence[str] = (),
    ) -> dict[str, tuple[object, ...]]:
        """The evidence alone, for callers that need nothing else."""

        perception = await self.perceive(
            portfolio,
            candidates=candidates,
            candidate_limit=candidate_limit,
            focus_symbols=focus_symbols,
        )

        return perception.evidence

    async def perceive(
        self,
        portfolio: PortfolioSnapshot,
        candidates: Sequence[ResearchCandidate] = (),
        candidate_limit: int = 0,
        focus_symbols: Sequence[str] = (),
    ) -> SecurityEvidence:
        """
        Return per-symbol evidence, and what was attempted to get it.

        `focus_symbols` are evidenced whatever the candidate budget says.
        A caller asking about one security is asking for that security to
        be looked at, and a cycle that answered without looking was
        answering about the account instead.
        """

        if not portfolio.holdings and not candidates and not focus_symbols:
            return SecurityEvidence()

        instruments = await self._symbol_resolver.items()

        targets = [
            (holding.symbol, instruments[holding.instrument_id])
            for holding in portfolio.holdings
            if holding.is_resolved and holding.instrument_id in instruments
        ]

        candidate_targets = self._candidate_targets(
            candidates,
            instruments,
            candidate_limit,
        )

        targets.extend(candidate_targets)

        attempted = tuple(symbol for symbol, _ in candidate_targets)

        targets.extend(
            self._focus_targets(
                focus_symbols,
                instruments,
                already_targeted={symbol.upper().strip() for symbol, _ in targets},
            )
        )

        if not targets:
            return SecurityEvidence(attempted_candidates=attempted)

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

        return SecurityEvidence(
            evidence=evidence,
            attempted_candidates=attempted,
        )

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

    @staticmethod
    def _focus_targets(
        focus_symbols: Sequence[str],
        instruments: dict[int, WatchlistItem],
        already_targeted: set[str],
    ) -> list[tuple[str, WatchlistItem]]:
        """
        Evidence the securities the caller actually asked about.

        A security the watchlists cannot describe still produces nothing.
        That is the same gap a holding hits when no watchlist names it, and
        it is reported as missing evidence rather than filled in.
        """

        by_symbol = {item.symbol.upper().strip(): item for item in instruments.values()}

        targets: list[tuple[str, WatchlistItem]] = []

        for symbol in focus_symbols:
            normalized = symbol.upper().strip()

            if normalized in already_targeted:
                continue

            item = by_symbol.get(normalized)

            if item is not None:
                targets.append((normalized, item))
                already_targeted.add(normalized)

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
