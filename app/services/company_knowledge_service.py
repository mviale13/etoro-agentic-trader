"""What this platform knows about a business, read once per filing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.knowledge_consensus import (
    QUORUM,
    CompanyKnowledgeConsensus,
    consensus_of,
)
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
    - `DOCUMENT_REFUSED` — the authoritative document exists, was
      retrieved and was parsed, and the section this platform needs
      cannot be supplied from the component or structure it supports.
      **Not a coverage gap**: another provider is not the remedy and an
      immediate retry cannot help, because nothing failed. A future
      capability — following the page ranges a cross-reference index
      names — may change the answer, which is what makes it different
      from a filing that simply does not contain the section.
    """

    AVAILABLE_CACHED = "available_cached"
    AVAILABLE_ACQUIRED = "available_acquired"
    UNAVAILABLE = "unavailable"
    PROVIDER_ERROR = "provider_error"
    INVALID_EXTRACTION = "invalid_extraction"
    DOCUMENT_REFUSED = "document_refused"

    @property
    def is_available(self) -> bool:
        return self in (
            KnowledgeState.AVAILABLE_CACHED,
            KnowledgeState.AVAILABLE_ACQUIRED,
        )

    @property
    def may_succeed_later(self) -> bool:
        """Whether asking again could plausibly produce a different answer.

        `DOCUMENT_REFUSED` is deliberately **false**. Nothing failed and
        nothing is intermittent: the filing says what it says, and the
        same request will be refused for the same structural reason for
        as long as this platform reads the same component. What could
        change the answer is a capability, not a retry.
        """

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
    knowledge: CompanyKnowledgeConsensus | None = None
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
        #
        # Composed on first use rather than here. This service is built
        # once per security on every page view, and composing the reader
        # resolves configuration and credentials into a live model
        # client — for a page that will only ever open the read-only
        # door. Only the two doors that can read a filing ask for it.
        self._extractor = extractor
        self._unreadable: str | None = None
        self._reader_composed = extractor is not None

    def _compose_reader(self) -> None:
        """Resolve the configured reader, the first time one is needed."""

        if self._reader_composed:
            return

        self._reader_composed = True

        resolved = resolve_reader()

        if isinstance(resolved, str):
            self._unreadable = resolved
        else:
            self._extractor = resolved

    async def knowledge(self, symbol: str) -> KnowledgeOutcome:
        """What is known about this company, reading a filing only if new.

        What comes back is a consensus, derived from the stored
        observations on this read and never stored itself. Acquisition
        still takes a single observation per new document — the quorum
        is filled by `observe`, explicitly, because five readings of
        every company's filing is a spend the platform takes knowingly
        rather than as a side effect of asking what it knows.
        """

        self._compose_reader()

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
                knowledge=self._latest(symbol),
                absent_because=str(unavailable),
            )

        observations = self._store.read(symbol, source.key)

        if observations:
            return KnowledgeOutcome(
                state=KnowledgeState.AVAILABLE_CACHED,
                knowledge=consensus_of(observations),
            )

        if self._extractor is None:
            return KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                knowledge=self._latest(symbol),
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
                knowledge=self._latest(symbol),
                absent_because=str(failure),
            )

        # **Before any model call.** A refused section is not a failed
        # reading: nothing was extracted, nothing failed grounding, and
        # nothing is written. `INVALID_EXTRACTION` would say the
        # opposite of all three, and it would bill for the privilege.
        if document.business_refusal is not None:
            return KnowledgeOutcome(
                state=KnowledgeState.DOCUMENT_REFUSED,
                knowledge=self._latest(symbol),
                absent_because=document.business_refusal.stated(),
            )

        try:
            extracted = await self._extractor.extract(symbol, document)
        except ExtractionRejected as rejected:
            # Nothing from a reading that failed its grounding contract
            # is stored, in part or at all.
            return KnowledgeOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                knowledge=self._latest(symbol),
                absent_because=str(rejected),
            )

        self._store.append(extracted)

        return KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            # Read back under the key the observation itself carries —
            # the store filed it there, and a reader whose document
            # identity differed from the resolved one would otherwise
            # produce an entry this consensus could not see.
            knowledge=consensus_of(self._store.read(symbol, extracted.source.key)),
        )

    async def observe(self, symbol: str, target: int = QUORUM) -> KnowledgeOutcome:
        """Take observations of the current document up to a count.

        The explicit spend that fills a consensus — to the quorum by
        default, or deeper where the spend is explicitly deeper. The
        stopping rule references only the count, fixed before anything
        is read and never what any observation says — which is what
        keeps this from being read-until-classifiable: an entry stops
        at its target whether its claims settled or not, and an
        unsettled consensus at the target is a finding, not a failure
        to keep asking. An entry already at the target observes nothing
        further.

        A reading refused by the grounding contract counts against
        nothing and is not retried here beyond the protocol's own
        bounded retries: the attempt is reported, and the observations
        that do exist keep serving at their stated width.
        """

        self._compose_reader()

        if self._extractor is None:
            return KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                knowledge=None,
                absent_because=(
                    self._unreadable
                    or "No reader is configured, so nothing can be observed."
                ),
            )

        try:
            source, provider = self._sources.resolve(symbol)
            document = provider.fetch(source)
        except PrimarySourceUnavailable as unavailable:
            return KnowledgeOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(unavailable, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                knowledge=self._latest(symbol),
                absent_because=str(unavailable),
            )

        # The same gate on the funded path, and it matters more here:
        # `observe` spends up to the quorum, so reading a refused
        # section would bill five model calls for a document that
        # carries no section to read.
        if document.business_refusal is not None:
            return KnowledgeOutcome(
                state=KnowledgeState.DOCUMENT_REFUSED,
                knowledge=self._latest(symbol),
                absent_because=document.business_refusal.stated(),
            )

        refused: str | None = None

        while len(self._store.read(symbol, source.key)) < target:
            try:
                observation = await self._extractor.extract(symbol, document)
            except ExtractionRejected as rejected:
                # One refusal ends the run rather than looping on a
                # document that resists reading; what was already
                # observed stands.
                refused = str(rejected)
                break

            self._store.append(observation)

        observations = self._store.read(symbol, source.key)

        if not observations:
            return KnowledgeOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                knowledge=None,
                absent_because=refused,
            )

        return KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            knowledge=consensus_of(observations),
            absent_because=refused,
        )

    def established(self, symbol: str) -> KnowledgeOutcome:
        """What is already known, without reading, fetching or spending.

        The read-only door, for surfaces rather than for acquisition.
        `knowledge` resolves the current document and reads it where it
        is new, which is right for a command an operator invoked and
        wrong for a page an investor loaded: it would put a network
        fetch and a model call behind a page view, and would quietly
        make the dashboard the thing that decides when this platform
        spends money.

        So this asks the store only. What comes back is the consensus
        over the newest filing this platform has already observed, which
        may be older than the filing that exists — a surface saying so
        is honest, and a surface that went and got it would not be a
        surface.
        """

        consensus = self._latest(symbol)

        if consensus is None:
            return KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                absent_because=(
                    f"No filing has been read for {symbol.upper().strip()}. "
                    "Reading one is an explicit spend, and no surface takes "
                    "it — `movrvest observe` does."
                ),
            )

        return KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge=consensus,
        )

    def _latest(self, symbol: str) -> CompanyKnowledgeConsensus | None:
        """Consensus over the newest document's observations, if any."""

        observations = self._store.latest(symbol)

        return consensus_of(observations) if observations else None
