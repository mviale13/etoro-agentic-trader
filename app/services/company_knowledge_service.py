"""What this platform knows about a business, read once per filing."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.company_knowledge import CompanyKnowledge
from app.domain.primary_source import PrimarySourceUnavailable
from app.providers.primary_source_provider import PrimarySourceResolver
from app.repositories.company_knowledge_store import (
    CompanyKnowledgeStore,
    JsonCompanyKnowledgeStore,
)
from app.services.company_knowledge_extractor import (
    CompanyKnowledgeExtractor,
    ExtractionRejected,
)


@dataclass(frozen=True, slots=True)
class KnowledgeOutcome:
    """What is known about a business, or why nothing is.

    Exactly one of the two is meaningful. An absence always carries its
    reason, because "this platform has not read a filing for BNP Paribas"
    and "BNP Paribas describes no segments" are different facts and a
    reader must not have to guess which one they are looking at.
    """

    knowledge: CompanyKnowledge | None = None
    absent_because: str | None = None


class CompanyKnowledgeService:
    """
    Structural knowledge, acquired once and kept.

    A primary source is immutable. Its key identifies one document
    forever — a regulator's accession number, or the hash of a published
    report — so knowledge read from it never needs reading again: not
    this cycle, not next quarter, not until the company publishes
    something newer.

    The saving is deliberate and it is not only the model call. Asking
    which document is current costs one small request; fetching it costs
    megabytes and extracting from it costs two model calls. A company
    whose latest document is already known pays the first and none of the
    rest.

    Which provider supplied the document is not this service's business.
    A European report reached through a different provider is acquired,
    extracted, stored and reused by exactly this path.

    Nothing here classifies. What kind of investment these facts add up
    to is a rule's decision, taken elsewhere, from knowledge that has
    already been grounded against the document it came from.
    """

    def __init__(
        self,
        store: CompanyKnowledgeStore | None = None,
        sources: PrimarySourceResolver | None = None,
        extractor: CompanyKnowledgeExtractor | None = None,
    ) -> None:
        self._store = store or JsonCompanyKnowledgeStore()
        self._sources = sources or PrimarySourceResolver()
        self._extractor = extractor

    async def knowledge(self, symbol: str) -> KnowledgeOutcome:
        """What is known about this company, reading a filing only if new."""

        try:
            source, provider = self._sources.resolve(symbol)
        except PrimarySourceUnavailable as unavailable:
            # No source any provider could resolve is a fact about this
            # platform's reach, and it is reported as one. Whatever the
            # store already holds from an earlier document still stands.
            known = self._store.latest(symbol)

            return KnowledgeOutcome(
                knowledge=known,
                absent_because=None if known is not None else str(unavailable),
            )

        stored = self._store.read(symbol, source.key)

        if stored is not None:
            return KnowledgeOutcome(knowledge=stored)

        if self._extractor is None:
            return KnowledgeOutcome(
                knowledge=self._store.latest(symbol),
                absent_because=(
                    f"{source.stated()} has not been read, and no reader is "
                    "configured to read it."
                ),
            )

        try:
            document = provider.fetch(source)
            extracted = await self._extractor.extract(symbol, document)
        except (PrimarySourceUnavailable, ExtractionRejected) as failure:
            return KnowledgeOutcome(
                knowledge=self._store.latest(symbol),
                absent_because=str(failure),
            )

        self._store.write(extracted)

        return KnowledgeOutcome(knowledge=extracted)
