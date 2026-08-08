"""How evidence identities and checked figures are written to disk.

One encoding per concept, shared by every store that keeps them. The
knowledge store and the statement store both file observations under a
`PrimarySource` and both keep `ReportedFigure`s, and two encodings of
one concept would eventually disagree about what a stored figure is —
the duplication invariant 9 removes everywhere else.

Decoding never repairs. A stored value that cannot be read back raises,
and the store that called decides what an unreadable entry means —
which, everywhere on this platform, is that it is absent and the
immutable document behind it is read again.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.domain.primary_source import (
    IdentityCheck,
    PrimarySource,
    ReportingPeriod,
    SourceAuthority,
    SourceType,
)
from app.domain.tabular_evidence import CellReference, ReportedFigure


def encode_source(source: PrimarySource) -> dict[str, Any]:
    """The document identity an entry is keyed by, as stored."""

    return {
        "symbol": source.symbol,
        "company": source.company,
        "source_type": source.source_type.value,
        "identifier": source.identifier,
        "key": source.key,
        "published_on": source.published_on.isoformat(),
        "reporting_period": encode_period(source.reporting_period),
        "document_format": source.document_format,
        "language": source.language,
        "location": source.location,
        "provider": source.provider,
        "authority": source.authority.value,
        "verification": [check.value for check in source.verification],
    }


def decode_source(stored: dict[str, Any]) -> PrimarySource:
    """The document identity an entry is keyed by, restored."""

    return PrimarySource(
        symbol=str(stored["symbol"]),
        company=str(stored["company"]),
        source_type=SourceType(stored["source_type"]),
        identifier=str(stored["identifier"]),
        key=str(stored["key"]),
        published_on=date.fromisoformat(stored["published_on"]),
        reporting_period=decode_period(stored.get("reporting_period")),
        document_format=str(stored["document_format"]),
        language=str(stored["language"]),
        location=str(stored["location"]),
        provider=str(stored["provider"]),
        authority=SourceAuthority(stored["authority"]),
        verification=tuple(
            IdentityCheck(value) for value in stored.get("verification", ())
        ),
    )


def encode_period(period: ReportingPeriod | None) -> dict[str, Any] | None:
    """The business period as stored, or nothing where none was."""

    if period is None:
        return None

    return {
        "ends_on": period.ends_on.isoformat(),
        "starts_on": (
            period.starts_on.isoformat() if period.starts_on is not None else None
        ),
    }


def decode_period(stored: Any) -> ReportingPeriod | None:
    """The business period as stored, or nothing where none was."""

    if not isinstance(stored, dict):
        return None

    starts = stored.get("starts_on")

    return ReportingPeriod(
        ends_on=date.fromisoformat(str(stored["ends_on"])),
        starts_on=date.fromisoformat(str(starts)) if starts is not None else None,
    )


def encode_figure(figure: ReportedFigure) -> dict[str, Any]:
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


def decode_figure(stored: Any) -> ReportedFigure:
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
