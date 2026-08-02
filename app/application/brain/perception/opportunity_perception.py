"""Perceive the securities the investor is watching but does not own."""

from __future__ import annotations

from app.domain.portfolio_snapshot import PortfolioSnapshot
from app.domain.research_candidate import ResearchCandidate
from app.services.watchlist_service import WatchlistService


class OpportunityPerception:
    """
    Report which watched securities are not already held.

    The investor's own watchlists are the candidate universe. Nothing is
    added to it: a security neither held nor watched is not silently
    introduced, because the platform has no evidence the investor is
    interested in it.
    """

    def __init__(
        self,
        watchlist_service: WatchlistService | None = None,
    ) -> None:
        self._watchlist_service = watchlist_service or WatchlistService()

    async def execute(
        self,
        portfolio: PortfolioSnapshot,
    ) -> tuple[ResearchCandidate, ...]:
        """Return every watched security the portfolio does not hold."""

        watchlists = await self._watchlist_service.get()

        held = {
            holding.symbol.upper().strip()
            for holding in portfolio.holdings
            if holding.symbol.strip()
        }

        candidates: dict[str, ResearchCandidate] = {}

        for watchlist in watchlists:
            for item in watchlist.items:
                symbol = item.symbol.upper().strip()

                if not symbol or symbol in held or symbol in candidates:
                    continue

                candidates[symbol] = ResearchCandidate(
                    symbol=symbol,
                    name=item.name,
                    source=watchlist.name,
                    instrument_id=item.instrument_id,
                )

        return tuple(candidates.values())
