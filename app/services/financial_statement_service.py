"""What this platform knows from a company's own statements, per filing."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.financial_statement_consensus import (
    FinancialStatementConsensus,
    authoritative,
    statement_consensus_of,
)
from app.domain.financial_statements import StatementKind
from app.domain.knowledge_consensus import QUORUM
from app.domain.primary_source import (
    PrimarySourceProviderError,
    PrimarySourceUnavailable,
)
from app.providers.primary_source_provider import PrimarySourceResolver
from app.repositories.financial_statement_store import (
    FinancialStatementStore,
    JsonFinancialStatementStore,
)
from app.services.company_knowledge_extractor import ExtractionRejected
from app.services.company_knowledge_reader import resolve_statement_reader
from app.services.company_knowledge_service import KnowledgeState
from app.services.financial_statement_extractor import FinancialStatementExtractor


@dataclass(frozen=True, slots=True)
class StatementOutcome:
    """What is known from the statements, how it was obtained, and why not.

    The same shape `KnowledgeOutcome` has, for the same reason: an
    absence always carries its reason, and knowledge and a
    non-available state can both be present — last filing's statements
    still stand when today's lookup fails.
    """

    state: KnowledgeState
    statements: FinancialStatementConsensus | None = None
    absent_because: str | None = None


class FinancialStatementService:
    """
    Filing-grade financial facts, acquired once per document and kept.

    The statement counterpart of `CompanyKnowledgeService`, sharing its
    economics deliberately: a primary source is immutable, so a reading
    of it never goes stale; asking what is known costs nothing beyond
    one observation per new document; and the quorum is filled by
    `observe`, explicitly, because five readings of every statement is
    a spend the platform takes knowingly rather than as a side effect
    of asking.

    Nothing here assesses. What these figures imply for any course is
    an assessment kind's business, designed after these facts exist —
    the sequence the accepted assessment design fixed.
    """

    def __init__(
        self,
        store: FinancialStatementStore | None = None,
        sources: PrimarySourceResolver | None = None,
        extractor: FinancialStatementExtractor | None = None,
    ) -> None:
        self._store = store or JsonFinancialStatementStore()
        self._sources = sources or PrimarySourceResolver()

        # Composed from configuration exactly as the knowledge reader
        # is, and a caller that supplies one is taken at its word.
        self._extractor = extractor
        self._unreadable: str | None = None

        if extractor is None:
            resolved = resolve_statement_reader()

            if isinstance(resolved, str):
                self._unreadable = resolved
            else:
                self._extractor = resolved

    async def statements(
        self,
        symbol: str,
        statement: StatementKind = StatementKind.INCOME_STATEMENT,
    ) -> StatementOutcome:
        """One statement's consensus, reading the filing only if new.

        One statement at a time, always. The three primary statements
        are three quorums that share a document key, and serving them
        together would hide which of them a caller has paid for.
        """

        try:
            source, provider = self._sources.resolve(symbol)
        except PrimarySourceUnavailable as unavailable:
            return StatementOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(unavailable, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                statements=self._latest(symbol, statement),
                absent_because=str(unavailable),
            )

        observations = self._store.read(symbol, source.key, statement)

        # Held readings that still carry authority. A document whose
        # every reading an audit withdrew has been read and is not
        # *known*, so it is read again rather than served from a set
        # that can no longer settle anything.
        if authoritative(observations):
            return StatementOutcome(
                state=KnowledgeState.AVAILABLE_CACHED,
                statements=statement_consensus_of(observations),
            )

        if self._extractor is None:
            return StatementOutcome(
                state=KnowledgeState.UNAVAILABLE,
                statements=self._latest(symbol, statement),
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
            return StatementOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(failure, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                statements=self._latest(symbol, statement),
                absent_because=str(failure),
            )

        try:
            extracted = await self._extractor.extract(symbol, document, statement)
        except ExtractionRejected as rejected:
            # Nothing from a reading that failed its checks is stored,
            # in part or at all.
            return StatementOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                statements=self._latest(symbol, statement),
                absent_because=str(rejected),
            )

        self._store.append(extracted)

        return StatementOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            statements=statement_consensus_of(
                self._store.read(symbol, extracted.source.key, statement)
            ),
        )

    async def observe(
        self,
        symbol: str,
        statement: StatementKind = StatementKind.INCOME_STATEMENT,
        target: int = QUORUM,
    ) -> StatementOutcome:
        """Take observations of one statement of the current document.

        The explicit spend that fills the statement consensus. The
        stopping rule references only the count, fixed before anything
        is read and never what any observation says — an entry stops
        at its target whether its claims settled or not, and an
        unsettled consensus at the target is a finding.
        """

        if self._extractor is None:
            return StatementOutcome(
                state=KnowledgeState.UNAVAILABLE,
                statements=None,
                absent_because=(
                    self._unreadable
                    or "No reader is configured, so nothing can be observed."
                ),
            )

        try:
            source, provider = self._sources.resolve(symbol)
            document = provider.fetch(source)
        except PrimarySourceUnavailable as unavailable:
            return StatementOutcome(
                state=(
                    KnowledgeState.PROVIDER_ERROR
                    if isinstance(unavailable, PrimarySourceProviderError)
                    else KnowledgeState.UNAVAILABLE
                ),
                statements=self._latest(symbol, statement),
                absent_because=str(unavailable),
            )

        refused: str | None = None

        # Counted over the readings that still carry authority, never
        # over everything stored. The target is untouched — five is
        # still five — but a superseded reading has no vote, so letting
        # it fill the count would mean an audited statement could never
        # be re-read and its authority never restored.
        while (
            len(authoritative(self._store.read(symbol, source.key, statement)))
            < target
        ):
            try:
                observation = await self._extractor.extract(symbol, document, statement)
            except ExtractionRejected as rejected:
                # One refusal ends the run rather than looping on a
                # document that resists reading; what was already
                # observed stands.
                refused = str(rejected)
                break

            self._store.append(observation)

        observations = self._store.read(symbol, source.key, statement)

        if not authoritative(observations):
            # Either nothing was ever read, or a refusal ended the run
            # before it could replace what an audit withdrew. Both are
            # "this statement has no authoritative account", and neither
            # is a consensus.
            return StatementOutcome(
                state=KnowledgeState.INVALID_EXTRACTION,
                statements=None,
                absent_because=refused,
            )

        return StatementOutcome(
            state=KnowledgeState.AVAILABLE_ACQUIRED,
            statements=statement_consensus_of(observations),
            absent_because=refused,
        )

    def established(
        self, symbol: str
    ) -> dict[StatementKind, FinancialStatementConsensus]:
        """Every statement already observed, without reading or spending.

        The read-only door, and the reason it exists is the same one
        `CompanyKnowledgeService.established` gives: `statements`
        resolves the current filing and reads it where it is new, which
        must never sit behind a page view.

        Returns only the statements this platform holds *with authority*.
        A statement absent from the mapping was never observed, or was
        observed and withdrawn — two different absences, told apart by
        `withdrawn`, and a consumer words whichever it is rather than
        filling either in.
        """

        held = {}

        for statement in StatementKind:
            consensus = self._latest(symbol, statement)

            if consensus is not None:
                held[statement] = consensus

        return held

    def withdrawn(self, symbol: str) -> dict[StatementKind, int]:
        """Statements held only as readings an audit withdrew, and how many.

        The other half of `established`, and the reason it exists is
        truthfulness. *"No statement has been read"* and *"every reading
        of it was superseded"* are different facts about this platform,
        and a surface that could not tell them apart would report a
        withdrawal as though the filing had never been opened.

        Read-only, like its sibling: it asks the store and stops.
        """

        withheld = {}

        for statement in StatementKind:
            observations = self._store.latest(symbol, statement)

            if observations and not authoritative(observations):
                withheld[statement] = len(observations)

        return withheld

    def _latest(
        self, symbol: str, statement: StatementKind
    ) -> FinancialStatementConsensus | None:
        """Consensus over the newest document's observations, if any."""

        # Filtered before the consensus is asked for, because a
        # statement whose every reading was superseded is one this
        # platform holds no authoritative account of — an absence a
        # surface words, not an error it raises.
        observations = authoritative(self._store.latest(symbol, statement))

        return statement_consensus_of(observations) if observations else None
