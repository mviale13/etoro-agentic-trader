"""Where what a company *is* is kept, as opposed to how it is doing."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.domain.company_knowledge import (
    BusinessSegment,
    CompanyKnowledge,
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
from app.domain.prose_evidence import DescribedSegment
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
KNOWLEDGE_SCHEMA_VERSION = 6


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
    """

    @abstractmethod
    def read(self, symbol: str, key: str) -> CompanyKnowledge | None:
        """What was read from this exact document, or nothing."""

    @abstractmethod
    def write(self, knowledge: CompanyKnowledge) -> None:
        """Keep what was read from a document."""

    @abstractmethod
    def latest(self, symbol: str) -> CompanyKnowledge | None:
        """
        The most recent filing's knowledge for this company.

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

    def read(self, symbol: str, key: str) -> CompanyKnowledge | None:
        path = self._path(symbol, key)

        if not path.exists():
            return None

        return self._restore(path)

    def write(self, knowledge: CompanyKnowledge) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)

        path = self._path(knowledge.symbol, knowledge.source.key)

        path.write_text(
            json.dumps(self._encode(knowledge), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def latest(self, symbol: str) -> CompanyKnowledge | None:
        known = [
            restored
            for path in self.directory.glob(f"{self._safe(symbol)}.*.json")
            if (restored := self._restore(path)) is not None
        ]

        if not known:
            return None

        # By the date the filing was received, not the date it was read.
        # Reading an older filing later must not make it the current word
        # on the company.
        return max(known, key=lambda item: item.source.published_on)

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
    def _encode(knowledge: CompanyKnowledge) -> dict[str, Any]:
        return {
            "schema_version": KNOWLEDGE_SCHEMA_VERSION,
            "symbol": knowledge.symbol,
            "description": knowledge.description,
            "segments": [
                {
                    "name": segment.name,
                    "revenue": _encode_share(segment.revenue),
                    "description": _encode_description(segment.description),
                    "undescribed_because": segment.undescribed_because,
                }
                for segment in knowledge.segments
            ],
            "source": {
                "symbol": knowledge.source.symbol,
                "company": knowledge.source.company,
                "source_type": knowledge.source.source_type.value,
                "identifier": knowledge.source.identifier,
                "key": knowledge.source.key,
                "published_on": knowledge.source.published_on.isoformat(),
                "reporting_period": _encode_period(knowledge.source.reporting_period),
                "document_format": knowledge.source.document_format,
                "language": knowledge.source.language,
                "location": knowledge.source.location,
                "provider": knowledge.source.provider,
                "authority": knowledge.source.authority.value,
                "verification": [
                    check.value for check in knowledge.source.verification
                ],
            },
            "reading": {
                "source": knowledge.reading.source,
                "observed_at": knowledge.reading.observed_at.isoformat(),
            },
        }

    def _restore(self, path: Path) -> CompanyKnowledge | None:
        """
        Read one stored filing back, or treat it as absent.

        An entry that cannot be read is not repaired. A guessed knowledge
        record would be indistinguishable from one taken off a filing,
        which is the one thing this store exists to keep apart.

        Nor is an entry written by an older extraction upgraded in place.
        Filling in what that reading never captured would be inventing
        it; the document is immutable and still available, so it is read
        again instead.
        """

        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

        if stored.get("schema_version") != KNOWLEDGE_SCHEMA_VERSION:
            # Read under an older extraction. Absent rather than partly
            # filled: the document is still there and can be read again.
            return None

        try:
            return CompanyKnowledge(
                symbol=str(stored["symbol"]),
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
                    )
                    for segment in stored.get("segments", ())
                ),
                source=PrimarySource(
                    symbol=str(stored["source"]["symbol"]),
                    company=str(stored["source"]["company"]),
                    source_type=SourceType(stored["source"]["source_type"]),
                    identifier=str(stored["source"]["identifier"]),
                    key=str(stored["source"]["key"]),
                    published_on=date.fromisoformat(stored["source"]["published_on"]),
                    reporting_period=_period(stored["source"].get("reporting_period")),
                    document_format=str(stored["source"]["document_format"]),
                    language=str(stored["source"]["language"]),
                    location=str(stored["source"]["location"]),
                    provider=str(stored["source"]["provider"]),
                    authority=SourceAuthority(stored["source"]["authority"]),
                    verification=tuple(
                        IdentityCheck(value)
                        for value in stored["source"].get("verification", ())
                    ),
                ),
                reading=Provenance(
                    source=str(stored["reading"]["source"]),
                    observed_at=datetime.fromisoformat(
                        stored["reading"]["observed_at"]
                    ),
                ),
            )
        except (KeyError, TypeError, ValueError, EvidenceNotApplicable):
            # A stored share whose two figures no longer hold together is
            # an entry that cannot be read, not one to be repaired. The
            # document is immutable and still there, so it is read again.
            return None


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
