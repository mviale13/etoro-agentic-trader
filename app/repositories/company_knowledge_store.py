"""Where what a company *is* is kept, as opposed to how it is doing."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
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
from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    ReportingPeriod,
    SourceAuthority,
    SourceType,
)
from app.domain.prose_evidence import DescribedSegment, Ownership
from app.domain.provenance import Provenance
from app.domain.tabular_evidence import (
    CellReference,
    MeasuredShare,
    ReportedFigure,
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
KNOWLEDGE_SCHEMA_VERSION = 9

#: The one older schema restored rather than treated as absent. See
#: above: a relabeling, not an upgrade.
RELABELED_SCHEMA_VERSION = 8


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
            "source": {
                "symbol": first.source.symbol,
                "company": first.source.company,
                "source_type": first.source.source_type.value,
                "identifier": first.source.identifier,
                "key": first.source.key,
                "published_on": first.source.published_on.isoformat(),
                "reporting_period": _encode_period(first.source.reporting_period),
                "document_format": first.source.document_format,
                "language": first.source.language,
                "location": first.source.location,
                "provider": first.source.provider,
                "authority": first.source.authority.value,
                "verification": [check.value for check in first.source.verification],
            },
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
            source = _source(stored["source"])
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


def _source(stored: dict[str, Any]) -> PrimarySource:
    """The document identity an entry is keyed by."""

    return PrimarySource(
        symbol=str(stored["symbol"]),
        company=str(stored["company"]),
        source_type=SourceType(stored["source_type"]),
        identifier=str(stored["identifier"]),
        key=str(stored["key"]),
        published_on=date.fromisoformat(stored["published_on"]),
        reporting_period=_period(stored.get("reporting_period")),
        document_format=str(stored["document_format"]),
        language=str(stored["language"]),
        location=str(stored["location"]),
        provider=str(stored["provider"]),
        authority=SourceAuthority(stored["authority"]),
        verification=tuple(
            IdentityCheck(value) for value in stored.get("verification", ())
        ),
    )


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
        "numerator": _encode_figure(share.numerator),
        "denominator": _encode_figure(share.denominator),
    }


def _encode_figure(figure: ReportedFigure) -> dict[str, Any]:
    """One printed number, with everything that says what it measures."""

    return {
        "label": figure.label,
        "column_header": figure.column_header,
        "printed": figure.printed,
        "value": figure.value,
        "caption": figure.caption,
        "cell": {
            "table": figure.cell.table,
            "row": figure.cell.row,
            "column": figure.cell.column,
        },
    }


def _share(stored: Any) -> MeasuredShare | None:
    """A segment's size as stored, or nothing where none was measured."""

    if not isinstance(stored, dict):
        return None

    return MeasuredShare(
        numerator=_figure(stored["numerator"]),
        denominator=_figure(stored["denominator"]),
    )


def _figure(stored: Any) -> ReportedFigure:
    """One printed number as stored."""

    return ReportedFigure(
        label=str(stored["label"]),
        column_header=str(stored["column_header"]),
        printed=str(stored["printed"]),
        value=float(stored["value"]),
        caption=str(stored.get("caption", "")),
        cell=CellReference(
            table=int(stored["cell"]["table"]),
            row=int(stored["cell"]["row"]),
            column=int(stored["cell"]["column"]),
        ),
    )


def _encode_period(period: ReportingPeriod | None) -> dict[str, Any] | None:
    """The business period as stored, or nothing where none was."""

    if period is None:
        return None

    return {
        "ends_on": period.ends_on.isoformat(),
        "starts_on": (
            period.starts_on.isoformat() if period.starts_on is not None else None
        ),
    }


def _period(stored: Any) -> ReportingPeriod | None:
    """The business period as stored, or nothing where none was."""

    if not isinstance(stored, dict):
        return None

    starts = stored.get("starts_on")

    return ReportingPeriod(
        ends_on=date.fromisoformat(str(stored["ends_on"])),
        starts_on=date.fromisoformat(str(starts)) if starts is not None else None,
    )
