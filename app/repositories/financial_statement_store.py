"""Where the figures a filer printed are kept, as observations.

The statement stream's own store, kept apart from the segment
observations on the pooling rule: the two readings are shown different
text, and a consensus over readings of different strings would call
the difference instability. Same architecture in everything else —
append-only, keyed by the document's immutable identity, never a
consensus on disk.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.evidence import EvidenceNotApplicable
from app.domain.financial_statements import (
    ConceptContract,
    FinancialStatementObservation,
    StatementConcept,
    StatementFact,
    StatementKind,
)
from app.domain.primary_source import PrimarySource
from app.domain.provenance import Provenance
from app.infrastructure.evidence_root import evidence_path
from app.repositories.source_codec import (
    decode_figure,
    decode_source,
    encode_figure,
    encode_source,
)

#: What this platform reads out of a primary statement, as a version.
#:
#: Its own counter, starting at 1, because the statement reading's
#: protocol moves independently of the segment reading's: entries here
#: are poolable only with entries shown the same statement section
#: under the same parse, and a version bump means the corpus of
#: statement observations is re-read — never the segment corpus, which
#: this stream cannot supersede.
#:
#: 1 — the stream begins: the income statement located where the filer
#: typeset its title, anchors checked by `figure_at`, rows read by the
#: platform.
#:
#: 2 — the statements are located as the run they form
#: (`app.providers.statement_locator`) rather than by the widest title
#: match. On JPMorgan that moves the balance sheet from the MD&A's
#: *Selected Consolidated balance sheets data* to the audited statement,
#: which is a different 3,554 characters — so schema-1 balance-sheet
#: readings and schema-2 ones were shown different text, and pooling
#: them would measure two strings and call the difference instability.
#:
#: The bump covers the whole stream rather than the one statement whose
#: text moved. The income statement and cash flow statement happen to
#: resolve to byte-identical sections, but *the protocol that produced
#: them changed*, and a version that tracked outcomes instead of
#: protocols would have to be re-argued at every locator change. The
#: corpus is re-read instead; the cost of that discipline here is
#: fifteen readings of one company.
#:
#: 3 — the income statement is asked two more concepts, `net_interest_income`
#: and `premium_revenue`, and the balance sheet accepts the parent's
#: equity stated with the filer's own name. Both change what a reading is
#: *asked*, not merely what it may answer: a schema-2 income-statement
#: reading was never shown the two new concepts, so pooling it with a
#: schema-3 one would report a concept as unaddressed by half the quorum
#: and call that a property of the filing. The corpus is re-read.
STATEMENT_SCHEMA_VERSION = 3


class FinancialStatementStore(ABC):
    """Durable statement observations, one entry per immutable document.

    An entry never expires: it is keyed by the document's own identity,
    and a filing under a given key is the same document forever. What
    an entry holds is observations, in the order they were taken; the
    consensus is derived on every read and never written down.
    """

    @abstractmethod
    def read(
        self, symbol: str, key: str, statement: StatementKind
    ) -> tuple[FinancialStatementObservation, ...]:
        """This statement's observations of this exact document, oldest first.

        Partitioned by statement, because a consensus is a property of
        one statement and `statement_consensus_of` refuses a mixed set
        outright. One document's three statements are three separate
        quorums that happen to share a key, and the store is where they
        are kept from meeting.
        """

    @abstractmethod
    def append(self, observation: FinancialStatementObservation) -> None:
        """Keep one more reading, after the ones the document has.

        Append-only. An observation is a record of what a reading
        found at a moment; replacing one would destroy the
        disagreement the consensus exists to measure.
        """

    @abstractmethod
    def latest(
        self, symbol: str, statement: StatementKind
    ) -> tuple[FinancialStatementObservation, ...]:
        """This statement's observations of the most recent filing."""

    @abstractmethod
    def supersede(self, symbol: str, key: str, reasons: Mapping[int, str]) -> int:
        """Record why numbered readings of this filing lost authority.

        Addressed by position in the entry's own observation list,
        which an append-only store makes stable: reading three is
        reading three forever.

        **Write-once.** A reading that already carries a reason keeps
        the reason it was given; a second audit may not restate, soften
        or clear it. That is what keeps this from becoming a general
        write door onto stored evidence — the only transition it can
        make is active to superseded, once, and the record of what the
        reading found is never touched.

        Returns how many readings this call newly superseded.
        """


class JsonFinancialStatementStore(FinancialStatementStore):
    """Statement observations on disk, one file per filing, kept indefinitely."""

    def __init__(
        self,
        directory: Path | str | None = None,
    ) -> None:
        # The evidence root, asked for rather than assumed. This store
        # named `data/statements` as a literal and was therefore the
        # one #118 missed: `MOVRVEST_EVIDENCE_ROOT` redirected every
        # cache and left this store reading the developer's real
        # corpus, so the suite's isolation did not cover it and BQ8's
        # experiment needed an explicit path to stay hermetic.
        #
        # Resolved *here* and never in the signature: a default
        # evaluated at import would freeze the root before a test could
        # redirect it, which is the same bug wearing a different hat —
        # and is exactly what ruff caught in three stores during #118.
        #
        # An explicit path still wins, unchanged: a caller that says
        # where its evidence lives is taken at its word.
        self.directory = (
            Path(directory) if directory is not None else evidence_path("statements")
        )

    def read(
        self, symbol: str, key: str, statement: StatementKind
    ) -> tuple[FinancialStatementObservation, ...]:
        path = self._path(symbol, key)

        if not path.exists():
            return ()

        return _only(self._restore(path), statement)

    def append(self, observation: FinancialStatementObservation) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

        path = self._path(observation.symbol, observation.source.key)

        existing = self._restore(path) if path.exists() else ()

        path.write_text(
            json.dumps(
                self._encode((*existing, observation)),
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def supersede(self, symbol: str, key: str, reasons: Mapping[int, str]) -> int:
        """Record why numbered readings of this filing lost authority."""

        path = self._path(symbol, key)
        existing = self._restore(path)

        if not existing:
            return 0

        superseded = 0
        rewritten: list[FinancialStatementObservation] = []

        for position, observation in enumerate(existing):
            reason = reasons.get(position)

            if reason is None or not observation.is_active:
                # Already superseded, or not named by this audit. Either
                # way the stored reason stands: write-once, so a second
                # audit cannot restate what the first concluded.
                rewritten.append(observation)
                continue

            rewritten.append(replace(observation, superseded_because=reason.strip()))
            superseded += 1

        if superseded:
            path.write_text(
                json.dumps(self._encode(tuple(rewritten)), indent=2, sort_keys=True),
                encoding="utf-8",
            )

        return superseded

    def latest(
        self, symbol: str, statement: StatementKind
    ) -> tuple[FinancialStatementObservation, ...]:
        known = [
            restored
            for path in self.directory.glob(f"{self._safe(symbol)}.*.json")
            if (restored := _only(self._restore(path), statement))
        ]

        if not known:
            return ()

        # By the date the filing was received, not the date it was
        # read. Reading an older filing later must not make it the
        # current word on the company.
        return max(known, key=lambda entry: entry[0].source.published_on)

    # ── on disk ─────────────────────────────────────────────────────

    def _path(self, symbol: str, key: str) -> Path:
        return self.directory / f"{self._safe(symbol)}.{self._safe(key)}.json"

    @staticmethod
    def _safe(value: str) -> str:
        return "".join(
            character if character.isalnum() or character in "-_" else "_"
            for character in value.upper().strip()
        )

    @staticmethod
    def _encode(
        observations: tuple[FinancialStatementObservation, ...],
    ) -> dict[str, Any]:
        """One document's entry: the source once, every observation of it."""

        first = observations[0]

        return {
            "schema_version": STATEMENT_SCHEMA_VERSION,
            "symbol": first.symbol,
            "source": encode_source(first.source),
            "observations": [
                {
                    "statement": observation.statement.value,
                    "located_among": observation.located_among,
                    # Written only where an audit set it, so a store of
                    # entirely active readings encodes byte-identically
                    # to one written before the field existed. An
                    # absent key is the default and reads as authority
                    # held, which is why no migration is needed.
                    **(
                        {"superseded_because": observation.superseded_because}
                        if observation.superseded_because is not None
                        else {}
                    ),
                    # Written only where a reading carried it, so an
                    # entry taken before acquisition stamped the
                    # producing contract re-encodes byte-identically.
                    # An absent key is "not recorded", never "today's".
                    **(
                        {
                            "produced_under": {
                                stamped.concept.value: stamped.fingerprint
                                for stamped in observation.produced_under
                            }
                        }
                        if observation.produced_under
                        else {}
                    ),
                    "facts": [
                        {
                            "concept": fact.concept.value,
                            "anchor": (
                                encode_figure(fact.anchor)
                                if fact.anchor is not None
                                else None
                            ),
                            "row": [encode_figure(figure) for figure in fact.row],
                            "unlocated_because": fact.unlocated_because,
                        }
                        for fact in observation.facts
                    ],
                    "reading": {
                        "source": observation.reading.source,
                        "observed_at": observation.reading.observed_at.isoformat(),
                    },
                }
                for observation in observations
            ],
        }

    def _restore(self, path: Path) -> tuple[FinancialStatementObservation, ...]:
        """
        Read one stored filing's observations back, or treat it as absent.

        An entry that cannot be read is not repaired, and an entry
        written by another schema version is not upgraded: a guessed
        record would be indistinguishable from one taken off a filing.
        The document is immutable and still there, so it is read again.
        """

        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ()

        if stored.get("schema_version") != STATEMENT_SCHEMA_VERSION:
            return ()

        try:
            source = decode_source(stored["source"])
            symbol = str(stored["symbol"])

            return tuple(
                _observation(symbol, source, observed)
                for observed in stored.get("observations", ())
            )
        except (KeyError, TypeError, ValueError, EvidenceNotApplicable):
            return ()


def _only(
    observations: tuple[FinancialStatementObservation, ...],
    statement: StatementKind,
) -> tuple[FinancialStatementObservation, ...]:
    """One statement's readings, in the order they were taken.

    One file holds one filing, and a filing has three statements — so
    the partition is applied on the way out rather than by writing three
    files. Which keeps the store's unit what it has always been: the
    immutable document.
    """

    return tuple(
        observation
        for observation in observations
        if observation.statement is statement
    )


def _stamped(stored: dict[str, Any]) -> dict[str, Any]:
    """The producing-contract fingerprints this entry recorded, if any."""

    recorded = stored.get("produced_under")

    return recorded if isinstance(recorded, dict) else {}


def _observation(
    symbol: str,
    source: PrimarySource,
    stored: dict[str, Any],
) -> FinancialStatementObservation:
    """One reading's body, restored exactly as it was taken."""

    return FinancialStatementObservation(
        symbol=symbol,
        statement=StatementKind(stored["statement"]),
        # Defaulted, never invented: an entry written before the count
        # existed records 0, which reads as "not recorded" rather than
        # as "one contender". Upgrading it in place would be filling in
        # what the reading never captured.
        located_among=int(stored.get("located_among", 0)),
        # Same rule, one field later: an entry no audit has ruled on
        # carries nothing here and still holds its authority. Absence is
        # the default rather than a claim that an audit cleared it.
        superseded_because=(
            str(stored["superseded_because"])
            if stored.get("superseded_because")
            else None
        ),
        # Read back, never recomputed. Recomputing would make every
        # stored reading claim it was produced under whatever contract
        # is running now, which is the one thing this field exists to
        # make impossible — an entry without it stays without it.
        # Restored in the vocabulary's own order rather than the JSON
        # object's, which `sort_keys` alphabetises: a decode that
        # depended on key order would make a promoted observation
        # unequal to the one it was copied from.
        produced_under=tuple(
            ConceptContract(
                concept=concept,
                fingerprint=str(_stamped(stored)[concept.value]),
            )
            for concept in StatementConcept
            if concept.value in _stamped(stored)
        ),
        facts=tuple(
            StatementFact(
                concept=StatementConcept(fact["concept"]),
                anchor=(
                    decode_figure(fact["anchor"])
                    if fact.get("anchor") is not None
                    else None
                ),
                row=tuple(decode_figure(figure) for figure in fact.get("row", ())),
                unlocated_because=(
                    str(fact["unlocated_because"])
                    if fact.get("unlocated_because")
                    else None
                ),
            )
            for fact in stored.get("facts", ())
        ),
        source=source,
        reading=Provenance(
            source=str(stored["reading"]["source"]),
            observed_at=datetime.fromisoformat(stored["reading"]["observed_at"]),
        ),
    )
