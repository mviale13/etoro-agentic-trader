"""Where what a company *is* is kept, as opposed to how it is doing."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledgeObservation,
    DescriptionRepair,
    RevenueModel,
    SegmentDescription,
)
from app.domain.evidence import EvidenceNotApplicable
from app.domain.primary_source import PrimarySource
from app.domain.prose_evidence import DescribedSegment, Ownership
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import MeasuredShare
from app.repositories.source_codec import (
    decode_figure,
    decode_source,
    encode_figure,
    encode_source,
)

#: What this platform reads out of a primary source, as a version.
#:
#: The source is immutable; the reading is not. When the extraction
#: starts capturing something it did not before — a reporting period, a
#: geography, a customer type — entries written under an older reading
#: are missing it, and they will never be refreshed on their own because
#: the document behind them has not changed.
#:
#: So a stored entry from an older reading is treated as absent, and the
#: document is read again under the current one. Immutable source,
#: versioned reading: the two are different things and only one of them
#: is fixed.
#: 7 — narrative ownership can now be structural. An entry written under
#: 6 had its descriptions placed by the nearest segment naming, which on
#: a filing that names its segments after describing them attributes the
#: prose backwards. Those entries are not repairable from what is stored,
#: because what was wrong is which region the words were read as
#: belonging to; the filing is immutable and still there, so it is read
#: again.
#: 8 — a section is located by the structure the filer typeset rather
#: than by width, and a missing size now carries its reason. An entry
#: written under 7 may have been read from a cross-reference to the
#: section instead of the section, which is not visible in what was
#: stored: the segments look ordinary and their sizes look absent from
#: the filing. Caterpillar's were, and they are printed in a table the
#: reading was never shown.
#: 9 — an entry holds *observations*, plural, because the calibration
#: measured that a reading of unchanged prose varies between runs, and
#: what the platform serves is the consensus derived over the set. A
#: schema-8 entry is the one cross-schema read this store performs: it
#: restores as a single observation, because that is exactly what it
#: always was, and relabeling a reading as one reading invents nothing.
#: The prohibition on upgrades exists to stop inventing what a reading
#: never captured; here nothing is filled in — the reading protocol did
#: not change between 8 and 9, only what the store calls the entry.
#: 10 — a section that says its content is printed elsewhere is now
#: followed, so the reader is shown a part of the filing that entries
#: written under 9 were never given. This is the case the version exists
#: for, in its plainest form: JPMorgan's Item 1 names its segments and
#: states that what they do is described in a chapter eighty pages
#: later, and every reading under 9 honestly reported that the filing
#: described nothing. Those entries are not wrong about what they were
#: shown, and that is exactly why they cannot be pooled with readings of
#: the wider text — a consensus over both would be measuring two
#: different strings and calling the difference instability, which is
#: the one thing `consensus_of` refuses across documents and must refuse
#: here for the same reason.
#: 11 — the tables are shown differently: a spanned group's words now
#: cover every column the filer's colspan asserted, a table split by
#: the page is read as the one table it is, and a pointer discussion is
#: served the referenced chapter's tables. An entry written under 10
#: had its sizes read from tables whose grouped columns carried no
#: header and whose totals sat in a separate physical table — JPMorgan's
#: sizes were absent for exactly that reason — and its mix reading was
#: shown different table text besides, so the readings are not poolable
#: and the documents are read again.
#: 12 — a segment the tagged text names and does not describe is now
#: asked about against the package's *untagged* documents: prose from
#: around the filer's own uses of the segment's name, in the management
#: report a multi-document package ships without a single XBRL tag.
#: Volkswagen's five readings under 11 each reported, honestly, that
#: nothing describes its segments — about tagged text that genuinely
#: describes nothing — while the division descriptions sat in a
#: thirteen-megabyte report the reading was never shown. This is schema
#: 10's case again in a second wardrobe: the reader is shown a part of
#: the filing that earlier entries were never given, so the readings
#: are not poolable and the documents, immutable and still there, are
#: read again. An EDGAR filing and a single-document ESEF package are
#: shown exactly the text 11 showed them, and their entries are read
#: again for the same reason 10 and 11 re-read everything: the version
#: stamps the protocol, and a protocol is one thing, not a per-document
#: negotiation.
KNOWLEDGE_SCHEMA_VERSION = 12

#: No older schema is restored. 8 was relabeled into 9 because nothing
#: about the reading had changed; every version since changed what the
#: reading was shown — so entries beneath the current version are absent
#: and the documents, immutable and still there, are read again.
RELABELED_SCHEMA_VERSION: int | None = None


class CompanyKnowledgeStore(ABC):
    """
    Durable structural knowledge about a business.

    Deliberately not the evidence store. Evidence is dynamic and
    time-sensitive — a price, a margin, an earnings date — and is fetched
    with a cadence and expires. What a company *is* changes when the
    company changes: its segments, what each sells, how it earns. That
    turns over across years, not minutes, and it is read from a document
    that cannot be revised.

    Which is why an entry never expires. It is keyed by the regulator's
    accession number, and a filing under a given accession is the same
    document forever, so knowledge read from it can be reused for as long
    as that filing stands as the company's latest word.

    What an entry holds is *observations* — every independent reading of
    that one document, in the order they were taken. The store never
    holds a consensus: consensus is derived from the observations on
    every read, so a changed rule leaves no stale conclusions behind it
    and there is no second place for an answer to be true.
    """

    @abstractmethod
    def read(self, symbol: str, key: str) -> tuple[CompanyKnowledgeObservation, ...]:
        """Every observation of this exact document, oldest first."""

    @abstractmethod
    def append(self, observation: CompanyKnowledgeObservation) -> None:
        """Keep one more reading of a document, after the ones it has.

        Append-only. An observation is a record of what a reading found
        at a moment; replacing one would destroy the disagreement the
        consensus exists to measure.
        """

    @abstractmethod
    def latest(self, symbol: str) -> tuple[CompanyKnowledgeObservation, ...]:
        """
        The most recent filing's observations for this company.

        What an analyst asks for: it knows the company, not which
        document last described it.
        """


class JsonCompanyKnowledgeStore(CompanyKnowledgeStore):
    """Knowledge on disk, one file per filing, kept indefinitely."""

    def __init__(
        self,
        directory: Path | str = "data/knowledge",
    ) -> None:
        self.directory = Path(directory)

    def read(self, symbol: str, key: str) -> tuple[CompanyKnowledgeObservation, ...]:
        path = self._path(symbol, key)

        if not path.exists():
            return ()

        return self._restore(path)

    def append(self, observation: CompanyKnowledgeObservation) -> None:
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

    def latest(self, symbol: str) -> tuple[CompanyKnowledgeObservation, ...]:
        known = [
            restored
            for path in self.directory.glob(f"{self._safe(symbol)}.*.json")
            if (restored := self._restore(path))
        ]

        if not known:
            return ()

        # By the date the filing was received, not the date it was read.
        # Reading an older filing later must not make it the current word
        # on the company.
        return max(known, key=lambda entry: entry[0].source.published_on)

    def documents(
        self, symbol: str
    ) -> tuple[tuple[CompanyKnowledgeObservation, ...], ...]:
        """Every stored filing's observations for this company.

        Each inner tuple is one document's observations, oldest first,
        exactly as `read` returns them; the outer tuple is ordered by
        the filing's `published_on`, oldest first. What the ledger's
        replay walks: `latest` answers what the current word is, and
        this answers everything the store can still restore — which is
        the honest bound on any history derived from it, because an
        entry an older schema wrote restores as absent here too.
        """

        return tuple(
            sorted(
                (
                    restored
                    for path in self.directory.glob(f"{self._safe(symbol)}.*.json")
                    if (restored := self._restore(path))
                ),
                key=lambda entry: entry[0].source.published_on,
            )
        )

    def symbols(self) -> tuple[str, ...]:
        """Every company the store holds any observation for, sorted.

        Read from the entries themselves rather than parsed back out of
        filenames: `_safe` flattens dots and filenames cannot be
        reversed, but every entry records the symbol it was filed for.
        """

        return tuple(
            sorted(
                {
                    restored[0].symbol
                    for path in self.directory.glob("*.json")
                    if (restored := self._restore(path))
                }
            )
        )

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
        observations: tuple[CompanyKnowledgeObservation, ...],
    ) -> dict[str, Any]:
        """One document's entry: the source once, every observation of it.

        The source is shared rather than repeated per observation
        because the entry is keyed by it — observations of two documents
        cannot share a file, and `append` never mixes them.
        """

        first = observations[0]

        return {
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "symbol": first.symbol,
            "source": encode_source(first.source),
            "observations": [
                {
                    "description": observation.description,
                    "segments": [
                        {
                            "name": segment.name,
                            "revenue": _encode_share(segment.revenue),
                            "description": _encode_description(segment.description),
                            "undescribed_because": segment.undescribed_because,
                            "unmeasured_because": segment.unmeasured_because,
                        }
                        for segment in observation.segments
                    ],
                    "reading": {
                        "source": observation.reading.source,
                        "observed_at": observation.reading.observed_at.isoformat(),
                    },
                }
                for observation in observations
            ],
        }

    def _restore(self, path: Path) -> tuple[CompanyKnowledgeObservation, ...]:
        """
        Read one stored filing's observations back, or treat it as absent.

        An entry that cannot be read is not repaired. A guessed knowledge
        record would be indistinguishable from one taken off a filing,
        which is the one thing this store exists to keep apart.

        Nor is an entry written by an older extraction upgraded in place
        — with one deliberate exception. A schema-8 entry restores as a
        single observation, because that is precisely what it always
        was: the reading protocol did not change between 8 and 9, only
        what the store calls the entry, and relabeling a reading as one
        reading invents nothing. Anything older is absent as before; the
        document is immutable and still there, so it is read again.
        """

        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ()

        version = stored.get("schema_version")

        try:
            source = decode_source(stored["source"])
            symbol = str(stored["symbol"])

            if version == RELABELED_SCHEMA_VERSION:
                return (_observation(symbol, source, stored),)

            if version != KNOWLEDGE_SCHEMA_VERSION:
                return ()

            return tuple(
                _observation(symbol, source, observed)
                for observed in stored.get("observations", ())
            )
        except (KeyError, TypeError, ValueError, EvidenceNotApplicable):
            # A stored share whose two figures no longer hold together is
            # an entry that cannot be read, not one to be repaired. The
            # document is immutable and still there, so it is read again.
            return ()


def _observation(
    symbol: str,
    source: PrimarySource,
    stored: dict[str, Any],
) -> CompanyKnowledgeObservation:
    """One reading's body — identical in shape under schema 8 and 9."""

    return CompanyKnowledgeObservation(
        symbol=symbol,
        description=str(stored["description"]),
        segments=tuple(
            BusinessSegment(
                name=str(segment["name"]),
                revenue=_share(segment.get("revenue")),
                description=_description(segment.get("description")),
                undescribed_because=(
                    str(segment["undescribed_because"])
                    if segment.get("undescribed_because")
                    else None
                ),
                unmeasured_because=(
                    str(segment["unmeasured_because"])
                    if segment.get("unmeasured_because")
                    else None
                ),
            )
            for segment in stored.get("segments", ())
        ),
        source=source,
        reading=Provenance(
            source=str(stored["reading"]["source"]),
            observed_at=datetime.fromisoformat(stored["reading"]["observed_at"]),
        ),
    )


def _encode_description(described: SegmentDescription | None) -> dict[str, Any] | None:
    """
    What a segment does, with the proof it is said of that segment.

    The naming and the distance are stored beside the words because they
    are what makes the words evidence rather than a quotation. An entry
    holding only the span would be indistinguishable from one written
    before applicability was checked at all.
    """

    if described is None:
        return None

    stored: dict[str, Any] = {
        "quoted": described.evidence.quoted,
        "under": described.evidence.under,
        "distance": described.evidence.distance,
        # Which mechanism established the ownership, because "inside the
        # section headed Reality Labs Products" and "51 characters after
        # a mention of Reality Labs" are different strengths of proof and
        # a reader is owed the difference.
        "ownership": described.evidence.ownership.value,
        "revenue_models": [model.value for model in described.revenue_models],
    }

    # Absent for a span the first reading got right, which is the
    # ordinary case and the one worth keeping small on disk.
    if described.repair is not None:
        stored["repair"] = {
            "first_refused_because": described.repair.first_refused_because,
            "reader": described.repair.reader,
        }

    return stored


def _description(stored: Any) -> SegmentDescription | None:
    """A segment's description as stored, or nothing where none applied."""

    if not isinstance(stored, dict):
        return None

    return SegmentDescription(
        evidence=DescribedSegment(
            quoted=str(stored["quoted"]),
            under=str(stored["under"]),
            distance=int(stored["distance"]),
            ownership=Ownership(stored["ownership"]),
        ),
        revenue_models=tuple(
            RevenueModel(value)
            for value in stored.get("revenue_models", ())
            if value in {model.value for model in RevenueModel}
        ),
        repair=_repair(stored.get("repair")),
    )


def _repair(stored: Any) -> DescriptionRepair | None:
    """How a span was arrived at, where it was not the first answer.

    Kept across the round trip because a repaired reading must never
    come back off disk looking like a first one. The schema version is
    what guarantees it: an entry written before repairs existed has no
    way to say whether its span was repaired, so it is re-read rather
    than assumed innocent.
    """

    if not isinstance(stored, dict):
        return None

    return DescriptionRepair(
        first_refused_because=str(stored["first_refused_because"]),
        reader=str(stored["reader"]),
    )


def _encode_share(share: MeasuredShare | None) -> dict[str, Any] | None:
    """
    A segment's size as the two printed figures it was measured from.

    The share itself is deliberately not written down. It is arithmetic
    over two figures, and storing the answer beside its inputs would
    create a second place for it to be true — where a later reader could
    trust a number nothing had checked. What is kept is the evidence,
    and the share is worked out from it every time it is asked for.
    """

    if share is None:
        return None

    return {
        "numerator": encode_figure(share.numerator),
        "denominator": encode_figure(share.denominator),
    }


def _share(stored: Any) -> MeasuredShare | None:
    """A segment's size as stored, or nothing where none was measured."""

    if not isinstance(stored, dict):
        return None

    return MeasuredShare(
        numerator=decode_figure(stored["numerator"]),
        denominator=decode_figure(stored["denominator"]),
    )
