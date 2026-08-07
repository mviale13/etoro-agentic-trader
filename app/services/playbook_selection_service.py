"""Serve one playbook selection under the migration rule.

The seam where the two selector routes meet without blending, per
`docs/architecture/PLAYBOOK_SELECTION.md`. The grounded route is tried
first and consumes only consensus knowledge; where it refuses — below
quorum, archetype undecided, conclusion unmapped, or no knowledge at
all — the pre-existing industry selector serves exactly as it always
has, and the selection records that it did, with the grounded route's
refusal verbatim.

What this module never does is combine them: no industry hint reaches
the grounded mapping, no consensus claim reaches the industry selector,
and a fallback selection's `facts_consumed` is empty because there is
genuinely nothing it consumed that traces to a filing.
"""

from __future__ import annotations

from typing import Any

from app.domain.playbook import PLAYBOOKS, PlaybookKind
from app.domain.playbook_selection import (
    PlaybookSelection,
    RefusedGrounding,
    SelectedBy,
)
from app.services.company_facts_service import CompanyFactsService
from app.services.company_knowledge_service import CompanyKnowledgeService
from app.services.company_profiler import CompanyProfiler
from app.services.playbook_mapping import select_grounded
from app.services.playbook_selector import PlaybookSelector
from app.services.understanding_engine import understand
from app.services.watchlist_service import WatchlistService


class PlaybookSelectionService:
    def __init__(
        self,
        *,
        knowledge: Any | None = None,
        watchlist: Any | None = None,
        facts: Any | None = None,
        profiler: CompanyProfiler | None = None,
        industry: PlaybookSelector | None = None,
    ) -> None:
        self._knowledge = knowledge or CompanyKnowledgeService()
        self._watchlist = watchlist or WatchlistService()
        self._facts = facts or CompanyFactsService()
        self._profiler = profiler or CompanyProfiler()
        self._industry = industry or PlaybookSelector()

    async def select(self, symbol: str) -> PlaybookSelection:
        """One selection, from whichever route has earned the right."""

        normalized = symbol.upper().strip()

        outcome = await self._knowledge.knowledge(normalized)

        if outcome.knowledge is not None:
            grounded = select_grounded(understand(outcome.knowledge))

            if isinstance(grounded, PlaybookSelection):
                return grounded

            refused = grounded
        else:
            refused = RefusedGrounding(
                because=outcome.absent_because
                or "No filing has been read for this security."
            )

        return await self._fallback(normalized, refused)

    async def _fallback(
        self,
        symbol: str,
        refused: RefusedGrounding,
    ) -> PlaybookSelection:
        """The industry route, served and labelled as what it is."""

        item = await self._watchlist.find_symbol(symbol)

        if item is None:
            playbook = PLAYBOOKS[PlaybookKind.UNCLASSIFIED]
            because = (
                "no provider profile could be built — the security is not "
                "on the investor's book — so even the industry route "
                "decided nothing"
            )
        else:
            profile = self._profiler.profile(await self._facts.build(item))
            playbook = self._industry.select(profile)
            because = (
                "the provider-reported industry names it; no consensus "
                "claim was consumed"
            )

        return PlaybookSelection(
            symbol=symbol,
            playbook=playbook,
            authoritative=False,
            selected_by=SelectedBy.REPORTED_INDUSTRY,
            selected_because=because,
            rule_fired=None,
            facts_consumed=(),
            narrowest_agreement=None,
            alternatives_considered=(),
            contingencies=(),
            fallback_reason=refused.because,
        )
