"""What this platform knows about a business, read once per filing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.company_knowledge import CompanyKnowledge
from app.domain.primary_source import (
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
)
from app.providers.primary_source_provider import PrimarySourceResolver
from app.repositories.company_knowledge_store import (
    CompanyKnowledgeStore,
    JsonCompanyKnowledgeStore,
)
from app.services.company_knowledge_extractor import (
    CompanyKnowledgeExtractor,
    ExtractionRejected,
)
from app.services.company_knowledge_reader import resolve_reader


class KnowledgeState(StrEnum):
    """How the knowledge in hand was — or was not — obtained.

    Operationally and semantically different situations that a single
    "no knowledge" would flatten into one. Each calls for something
    different:

    - `AVAILABLE_CACHED` — read from a document already extracted. The
      normal path, and free.
    - `AVAILABLE_ACQUIRED` — a new document was fetched and read this
      cycle. Costs a fetch and two model calls, once per document.
    - `UNAVAILABLE` — no provider holds a source for this security. A
      gap in coverage: try another provider, not the same one again.
    - `PROVIDER_ERROR` — a provider could not be reached. Retrying may
      help, which is exactly what makes it different from a gap.
    - `INVALID_EXTRACTION` — a document was read and failed grounding
      validation. Nothing from it is trusted or partly stored.
    """

    AVAILABLE_CACHED = "available_cached"
    AVAILABLE_ACQUIRED = "available_acquired"
    UNAVAILABLE = "unavailable"
    PROVIDER_ERROR = "provider_error"
    INVALID_EXTRACTION = "invalid_extraction"

    @property
    def is_available(self) -> bool:
        return self in (
            KnowledgeState.AVAILABLE_CACHED,
            KnowledgeState.AVAILABLE_ACQUIRED,
        )

    @property
    def may_succeed_later(self) -> bool:
        """Whether asking again could plausibly produce a different answer."""

        return self is KnowledgeState.PROVIDER_ERROR


@dataclass(frozen=True, slots=True)
class KnowledgeOutcome:
    """What is known about a business, how it was obtained, and why not.

    An absence always carries its reason, because "this platform has not
    read a filing for BNP Paribas" and "BNP Paribas describes no
    segments" are different facts and a reader must not have to guess
    which one they are looking at.

    Knowledge and a non-available state can both be present: last year's
    filing still describes the business when today's lookup fails, and
    the state says the reading is the older one.
    """

    state: KnowledgeState
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

        # The reader is composed from configuration rather than passed
        # in, so the pipeline reads filings by default. A caller that
        # supplies one is taken at its word and nothing is resolved:
        # inspecting what it handed over — asking whether it is really a
        # `CompanyKnowledgeExtractor` — would reject every stand-in that
        # answers the same way, which is the whole point of the seam.
        #
        # `resolve_reader` returns the worded reason when it cannot be
        # built, and that sentence is carried to the surface exactly as
        # an outage or a gap in coverage is.
        self._extractor = extractor
        self._unreadable: str | None = None

        if extractor is None:
            resolved = resolve_reader()

            if isinstance(resolved, str):
                self._unreadable = resolved
            else:
                self._extractor = resolved

    async def knowledge(self, symbol: str) -> KnowledgeOutcome:
        """What is known about this company, reading a filing only if new."""

        try:
            source, provider = self._sources.resolve(symbol)
        except PrimarySourceUnavailable as unavailable:
            # An outage and a gap in coverage are different answers, and
            # only one is worth asking about again. Whatever the store
            # already holds from an earlier document still stands.
            return KnowledgeOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(unavailable, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                knowledge=self._store.latest(symbol),
                absent_because=str(unavailable),
            )

        stored = self._store.read(symbol, source.key)

        if stored is not None:
            return KnowledgeOutcome(
                state=KnowledgeState.AVAILABLE_CACHED,
                knowledge=stored,
            )

        if self._extractor is None:
            return KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                knowledge=self._store.latest(symbol),
                absent_because=(
                    f"{source.stated()} has not been read. {self._unreadable}"
                    if self._unreadable
                    else (
                        f"{source.stated()} has not been read, and no reader "
                        "is configured to read it."
                    )
                ),
            )

        try:
            document = provider.fetch(source)
        except PrimarySourceUnavailable as failure:
            return KnowledgeOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(failure, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                knowledge=self._store.latest(symbol),
                absent_because=str(failure),
            )

        try:
            extracted = await self._extractor.extract(symbol, document)
        except ExtractionRejected as rejected:
            # Nothing from a reading that failed its grounding contract
            # is stored, in part or at all.
            return KnowledgeOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                knowledge=self._store.latest(symbol),
                absent_because=str(rejected),
            )

        self._store.write(extracted)

        return KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            knowledge=extracted,
        )
