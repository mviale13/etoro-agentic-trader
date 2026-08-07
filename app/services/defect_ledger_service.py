"""Replay the store's readings into the reader defect ledger.

Read-only over the local store: no document is resolved, fetched or
read, and no model is asked. The store is append-only and every
observation is dated, so what the platform served after any given
reading is derivable — this service walks each company's readings in
the order they were taken, derives the consensus that was current after
each one, and classifies its absences with the same `defects_of` the
taxonomy uses. The final replay state therefore *is* the taxonomy's
answer, which is what lets the ledger say "still found" and mean it.

What the replay walks is what the store restores, no further back. A
reading an older schema wrote restores as absent, and a reading the
grounding contract refused stored nothing to begin with; history before
either begins where the store's memory does, and the surface says so
rather than presenting the reachable history as the whole of it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.domain.company_knowledge import CompanyKnowledgeObservation
from app.domain.defect_ledger import (
    CLAIMED_RESOLUTIONS,
    DefectInstance,
    DefectLedger,
)
from app.domain.knowledge_consensus import consensus_of
from app.domain.reader_defects import Claim, DefectCause, defects_of
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore


class DefectLedgerService:
    def __init__(self, store: Any | None = None) -> None:
        self._store = store or JsonCompanyKnowledgeStore()

    def ledger(self) -> DefectLedger:
        instances: list[DefectInstance] = []
        scanned: list[str] = []

        for symbol in self._store.symbols():
            documents = self._store.documents(symbol)

            if not documents:
                continue

            scanned.append(symbol)
            instances.extend(_replay(symbol, documents))

        return DefectLedger(
            scanned=tuple(scanned),
            instances=tuple(instances),
            claims=CLAIMED_RESOLUTIONS,
        )


def _replay(
    symbol: str,
    documents: tuple[tuple[CompanyKnowledgeObservation, ...], ...],
) -> tuple[DefectInstance, ...]:
    """One company's readings, re-served in the order they were taken.

    After every reading, the consensus the platform served is the one
    over the then-current document — current by `published_on`, exactly
    the rule `latest` applies, so reading an older filing late never
    replays as it having been the current word. Each absent claim's
    appearance and disappearance in that served consensus is what an
    instance records.
    """

    events = sorted(
        (
            (observations[position].reading.observed_at, index, position)
            for index, observations in enumerate(documents)
            for position in range(len(observations))
        ),
    )

    #: How many of each document's observations the replay has seen.
    #: Visibility is by stored prefix: observations were appended in
    #: the order they were taken, and a consensus at a moment is over
    #: the readings that existed then.
    visible = [0] * len(documents)

    lifetimes: dict[tuple[str, Claim, DefectCause], tuple[datetime, datetime]] = {}
    present: set[tuple[str, Claim, DefectCause]] = set()

    for observed_at, index, _position in events:
        visible[index] += 1

        current = max(
            (index for index, count in enumerate(visible) if count),
            key=lambda index: documents[index][0].source.published_on,
        )

        consensus = consensus_of(documents[current][: visible[current]])

        present = {
            (defect.segment, defect.claim, defect.cause)
            for defect in defects_of(symbol, consensus)
        }

        for key in present:
            first, _last = lifetimes.get(key, (observed_at, observed_at))
            lifetimes[key] = (first, observed_at)

    return tuple(
        DefectInstance(
            symbol=symbol,
            segment=segment,
            claim=claim,
            cause=cause,
            first_observed=first,
            last_observed=last,
            still_found=(segment, claim, cause) in present,
        )
        for (segment, claim, cause), (first, last) in sorted(
            lifetimes.items(),
            key=lambda item: (item[1][0], item[0][0], item[0][1], item[0][2]),
        )
    )
