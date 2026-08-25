"""What this platform knows about a business, read once per filing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.knowledge_acquisition import KnowledgeAcquisitionEvent
from app.domain.knowledge_consensus import (
    QUORUM,
    CompanyKnowledgeConsensus,
    consensus_of,
)
from app.domain.knowledge_state import KnowledgeState as KnowledgeState
from app.domain.primary_source import (
    PrimarySource,
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
)
from app.infrastructure.evidence.knowledge_outcome_store import (
    KnowledgeOutcomeStore,
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


@dataclass(slots=True)
class _Attempt:
    """What one acquisition path learned about itself, as it learned it.

    Filled in by the body and read once by the recorder, so composing
    the terminal event needs one call site rather than one per return
    branch. Deliberately mutable and deliberately private: it is a
    scratchpad for a single call, never a stored shape.

    `failure` holds an exception **class name**, never a message. A
    provider message may carry an API key, a signed URL, an account
    identifier or a fragment of the document itself, and this record is
    written to disk.
    """

    source_key: str | None = None
    source_published: str = ""
    failure: str = ""
    observations_after: int = 0
    ended_in_refusal: bool = False
    usable_source_key: str | None = None


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
        outcomes: KnowledgeOutcomeStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store or JsonCompanyKnowledgeStore()
        self._sources = sources or PrimarySourceResolver()

        # The acquisition-outcome journal. Written by the two funded
        # doors and by nothing else — `established()` never touches it,
        # because a page view is not an attempt. The clock is a seam so
        # the attempted-at contract is deterministic in tests.
        self._outcomes = outcomes or KnowledgeOutcomeStore()
        self._clock = clock or (lambda: datetime.now(UTC))

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
        """The funded door, and the one terminal event it records."""

        return await self._recorded(symbol, self._knowledge)

    async def observe(self, symbol: str, target: int = QUORUM) -> KnowledgeOutcome:
        """The funded door that fills a quorum, and its terminal event."""

        return await self._recorded(
            symbol, lambda s, a: self._observe(s, a, target=target)
        )

    async def _recorded(
        self,
        symbol: str,
        run: Callable[[str, _Attempt], Awaitable[KnowledgeOutcome]],
    ) -> KnowledgeOutcome:
        """Run one funded attempt, then append exactly one event.

        **`attempted_at` means attempted-at.** The clock is read before
        the funded body begins, because an extraction can take long
        enough that a stamp taken afterwards would date the attempt by
        its outcome. Capturing a time is not writing an event: the
        append still happens only after the outcome is known, so a
        killed attempt carries its captured time nowhere.

        **Ordering is the contract.** The body writes any observation it
        takes to the knowledge store first; this appends afterwards, so
        a process killed between the two leaves the knowledge usable and
        invents no attempt outcome. There is no `try/finally` here on
        purpose: a hard kill must produce *no* terminal event rather
        than a manufactured one, so an exception escaping the body
        propagates and nothing is written.
        """

        attempt = _Attempt()
        attempted_at = self._clock()

        outcome = await run(symbol, attempt)

        self._outcomes.append(
            KnowledgeAcquisitionEvent(
                symbol=symbol,
                attempted_at=attempted_at,
                state=outcome.state,
                source_key=attempt.source_key,
                source_published=attempt.source_published,
                because=_safe_reason(outcome, attempt),
                knowledge_usable=outcome.knowledge is not None,
                usable_source_key=attempt.usable_source_key,
                observations_after=attempt.observations_after,
                ended_in_refusal=attempt.ended_in_refusal,
            )
        )

        return outcome

    async def _knowledge(self, symbol: str, attempt: _Attempt) -> KnowledgeOutcome:
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
            #
            # No source key is recorded: resolution is what failed, and
            # *we could not find a filing* is a different fact from *we
            # found one and could not read it*.
            attempt.failure = type(unavailable).__name__
            self._note_usable(symbol, attempt)

            return KnowledgeOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(unavailable, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                knowledge=self._latest(symbol),
                absent_because=str(unavailable),
            )

        attempt.source_key = source.key
        attempt.source_published = _published(source)

        observations = self._store.read(symbol, source.key)

        if observations:
            attempt.observations_after = len(observations)
            attempt.usable_source_key = source.key

            return KnowledgeOutcome(
                state=KnowledgeState.AVAILABLE_CACHED,
                knowledge=consensus_of(observations),
            )

        if self._extractor is None:
            attempt.failure = "NoReaderConfigured"
            self._note_usable(symbol, attempt)

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
            attempt.failure = type(failure).__name__
            self._note_usable(symbol, attempt)

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
            self._note_usable(symbol, attempt)

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
            attempt.failure = type(rejected).__name__
            attempt.ended_in_refusal = True
            self._note_usable(symbol, attempt)

            return KnowledgeOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                knowledge=self._latest(symbol),
                absent_because=str(rejected),
            )

        # The knowledge write lands before any event claims usable
        # acquired knowledge — the ordering the outcome journal's
        # durability contract rests on.
        self._store.append(extracted)

        stored = self._store.read(symbol, extracted.source.key)
        attempt.observations_after = len(stored)
        attempt.usable_source_key = extracted.source.key

        return KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            # Read back under the key the observation itself carries —
            # the store filed it there, and a reader whose document
            # identity differed from the resolved one would otherwise
            # produce an entry this consensus could not see.
            knowledge=consensus_of(self._store.read(symbol, extracted.source.key)),
        )

    async def _observe(
        self, symbol: str, attempt: _Attempt, target: int = QUORUM
    ) -> KnowledgeOutcome:
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
            attempt.failure = "NoReaderConfigured"
            # Before source resolution, so the refused attempt costs no
            # provider call — and what the store already holds from an
            # earlier document still stands, on this path as on every
            # other non-available terminal path.
            self._note_usable(symbol, attempt)

            return KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                knowledge=self._latest(symbol),
                absent_because=(
                    self._unreadable
                    or "No reader is configured, so nothing can be observed."
                ),
            )

        try:
            source, provider = self._sources.resolve(symbol)
            attempt.source_key = source.key
            attempt.source_published = _published(source)
            document = provider.fetch(source)
        except PrimarySourceUnavailable as unavailable:
            attempt.failure = type(unavailable).__name__
            self._note_usable(symbol, attempt)

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
            self._note_usable(symbol, attempt)

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
                attempt.failure = type(rejected).__name__
                attempt.ended_in_refusal = True
                break

            self._store.append(observation)

        observations = self._store.read(symbol, source.key)
        attempt.observations_after = len(observations)

        if not observations:
            # Nothing from the current document survived, and an older
            # document's knowledge — where one exists — still stands.
            self._note_usable(symbol, attempt)

            return KnowledgeOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                knowledge=self._latest(symbol),
                absent_because=refused,
            )

        attempt.usable_source_key = source.key

        # **The case that earned the separate event object.** Some
        # observations were taken and a later extraction was refused:
        # the knowledge is real and the run ended in a refusal, and no
        # single `KnowledgeState` can say both. The state stays
        # AVAILABLE_ACQUIRED, which is true, and `ended_in_refusal`
        # carries the other half beside it rather than overloading the
        # state into a lie in the opposite direction.
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
            # **This stream, and no claim about any other.** The sentence
            # here said "No filing has been read" — a claim about
            # filings, which this service is not in a position to make.
            # It reads one stream: the business description a filer
            # prints under Item 1, its segments and their sizes. Financial
            # statements are a separate observation stream with a separate
            # quorum, deliberately never pooled with these, and a company
            # can have one without the other.
            #
            # Disney is exactly that company. Its dossier reported "No
            # filing has been read for DIS" beside revenue and earnings
            # growth computed from 10-K 0001744489-25-000155, period ended
            # 2025-09-27, via SEC EDGAR — a filing this platform had
            # plainly read. The absence was real and the sentence
            # describing it was false, which is worse than either alone:
            # an investor reading both concluded the figures were
            # unsourced.
            #
            # So it now names what is missing rather than what has not
            # happened. No symbol is special-cased and nothing consults
            # the statement stream from here: a sentence that only speaks
            # for its own evidence cannot contradict evidence it does not
            # own.
            return KnowledgeOutcome(
                state=KnowledgeState.UNAVAILABLE,
                absent_because=(
                    "No business description has been read for "
                    f"{symbol.upper().strip()}: this platform holds no "
                    "reading of what the company says it does, or of its "
                    "segments and their sizes. Reading one is an explicit "
                    "spend, and no surface takes it — `movrvest observe` "
                    "does. Financial statements are read separately and "
                    "may be held regardless."
                ),
            )

        return KnowledgeOutcome(
            state=KnowledgeState.AVAILABLE_CACHED,
            knowledge=consensus,
        )

    def _note_usable(self, symbol: str, attempt: _Attempt) -> None:
        """Record what still serves beside an outcome that acquired nothing.

        The first dimension, read where the second has already failed:
        last year's filing still describes the business when today's
        lookup does not.
        """

        held = self._store.latest(symbol)

        if held:
            attempt.observations_after = len(held)
            attempt.usable_source_key = held[0].source.key

    def _latest(self, symbol: str) -> CompanyKnowledgeConsensus | None:
        """Consensus over the newest document's observations, if any."""

        observations = self._store.latest(symbol)

        return consensus_of(observations) if observations else None


def _published(source: PrimarySource) -> str:
    """The document's own publication date, ISO-formatted.

    `published_on` is the canonical field and it is required on
    `PrimarySource`, so a resolved source always carries one. The
    journal's `source_published` stays empty only where no source was
    resolved at all — the attempt scratchpad's own default, never a
    probe of a field that might not exist. The first cut of this
    helper read `.published` through `getattr`, a field no source has
    ever had, so every event recorded an empty date while claiming the
    source was resolved; typing the parameter is what makes that
    mistake unwritable.
    """

    return source.published_on.isoformat()


def _safe_reason(outcome: KnowledgeOutcome, attempt: _Attempt) -> str:
    """Why, in wording that may be written to disk.

    **A raw provider or extraction message is never persisted.** Those
    strings are composed by libraries this platform does not control and
    have carried API keys, signed URLs, account identifiers and document
    fragments. What survives is the exception *class*, which names the
    kind of failure and can carry nothing else.

    A document refusal is the one exception, and it is not one: its
    wording comes from `business_refusal.stated()` — a typed carrier
    this platform composed itself — so quoting it discloses nothing a
    provider put there.
    """

    if outcome.state is KnowledgeState.DOCUMENT_REFUSED:
        return (outcome.absent_because or "").strip()

    return attempt.failure
