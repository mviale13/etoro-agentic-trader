"""Scan the store's absent claims into the reader defect taxonomy.

Read-only over the local store, like the coverage report beside it: no
document is resolved, fetched or read, and no model is asked. For each
company the current document's consensus is derived and every absent
claim's stored reason is classified — the same `consensus_of` the
decision path uses, so the taxonomy counts exactly the absences the
platform serves, no more and no fewer.
"""

from __future__ import annotations

from typing import Any

from app.domain.knowledge_consensus import consensus_of
from app.domain.reader_defects import (
    DefectTaxonomy,
    ReaderDefect,
    defects_of,
)
from app.repositories.company_knowledge_store import JsonCompanyKnowledgeStore


class ReaderDefectService:
    def __init__(self, store: Any | None = None) -> None:
        self._store = store or JsonCompanyKnowledgeStore()

    def taxonomy(self) -> DefectTaxonomy:
        defects: list[ReaderDefect] = []
        scanned: list[str] = []

        for symbol in self._store.symbols():
            observations = self._store.latest(symbol)

            if not observations:
                continue

            scanned.append(symbol)
            defects.extend(defects_of(symbol, consensus_of(observations)))

        return DefectTaxonomy(scanned=tuple(scanned), defects=tuple(defects))
