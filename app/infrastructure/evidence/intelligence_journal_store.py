"""An append-only record of what was observed, one line at a time.

JSON Lines, one file per asset, opened in append mode and never in
write mode. That is the whole design, and the constraint is the point:
there is no code path here that can rewrite a line, because a store that
*could* rewrite history would eventually be asked to.

Reading is the ordinary case and it is tolerant — a line that cannot be
decoded is skipped rather than raising, because one bad line must not
cost the record. Writing is the guarded case: appends only, and a
capture already present is not written twice.

**Schema is carried per line, not per file.** Every other store on this
platform versions the file, which works when a file is rewritten whole;
this one never is, so a line written under schema 1 must stay readable
beside a line written under schema 2 forever. Migrating it would mean
rewriting history, which is the one thing the file exists to prevent.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.crypto_intelligence import ClaimType, EventKind
from app.domain.intelligence_journal import (
    Capture,
    JournalEntry,
    ObservationStatus,
)
from app.infrastructure.evidence_root import evidence_path

#: The line format's own version, written on every line.
SCHEMA = 1


class IntelligenceJournalStore:
    """The record. Appends, reads, and cannot do anything else."""

    def __init__(self, root: Path | str | None = None) -> None:
        # Resolved here rather than in the signature: a default
        # evaluated at import would freeze the root and ignore
        # every later redirection, which is the same class of
        # undeclared input this indirection exists to remove.
        self._root = Path(root) if root is not None else evidence_path("journal")

    def path_for(self, asset: str) -> Path:
        return self._root / f"{asset.upper().strip()}.jsonl"

    # ── writing ─────────────────────────────────────────────────────

    def append(self, capture: Capture) -> bool:
        """Add one capture. Returns False if it was already recorded.

        Idempotent on `capture_id`, which is derived from the asset, the
        moment and the content — so replaying *the same* capture is a
        no-op, while looking again an hour later is a second capture
        even if nothing changed.

        That second behaviour is deliberate and is the honest one: this
        platform did look twice, and the count of times it looked is
        exactly the fact §5 says a temporal claim must be built from.
        Collapsing two identical looks into one would make the record
        say it observed less than it did.
        """

        if not capture.entries:
            return False

        if self.holds(capture.asset, capture.capture_id):
            return False

        path = self.path_for(capture.asset)

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("a", encoding="utf-8") as handle:
            for entry in capture.entries:
                handle.write(json.dumps(_encode(entry), sort_keys=True))
                handle.write("\n")

        return True

    def holds(self, asset: str, capture_id: str) -> bool:
        return any(entry.capture_id == capture_id for entry in self._entries(asset))

    # ── reading ─────────────────────────────────────────────────────

    def captures(self, asset: str, limit: int | None = None) -> list[Capture]:
        """Every capture for this asset, oldest first.

        Entries are grouped back into the run that wrote them, so a
        caller reasons about *what one look saw* rather than about a
        flat list of readings from different moments.
        """

        grouped: dict[str, list[JournalEntry]] = {}

        for entry in self._entries(asset):
            grouped.setdefault(entry.capture_id, []).append(entry)

        captures = [
            Capture(
                capture_id=capture_id,
                asset=asset.upper().strip(),
                captured_at=min(entry.captured_at for entry in entries),
                entries=tuple(entries),
            )
            for capture_id, entries in grouped.items()
        ]

        captures.sort(key=lambda capture: capture.captured_at)

        return captures[-limit:] if limit else captures

    def _entries(self, asset: str) -> Iterator[JournalEntry]:
        path = self.path_for(asset)

        if not path.exists():
            return

        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    # One unreadable line must not cost the record.
                    continue

                entry = _decode(row)

                if entry is not None:
                    yield entry


# ── the line format ─────────────────────────────────────────────────


def _encode(entry: JournalEntry) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "capture_id": entry.capture_id,
        "asset": entry.asset,
        "captured_at": entry.captured_at.isoformat(),
        "key": entry.key,
        "family": entry.family.value,
        "claim_type": entry.claim_type.value,
        "status": entry.status.value,
        "stated": entry.stated,
        "value": entry.value,
        "unit": entry.unit,
        "source": entry.source,
        "source_observed_at": (
            entry.source_observed_at.isoformat() if entry.source_observed_at else None
        ),
        "refs": list(entry.refs),
        "corrects": entry.corrects,
    }


def _decode(row: Any) -> JournalEntry | None:
    if not isinstance(row, dict):
        return None

    try:
        return JournalEntry(
            capture_id=str(row["capture_id"]),
            asset=str(row["asset"]),
            captured_at=_time(row["captured_at"]) or datetime.now(UTC),
            key=str(row["key"]),
            family=EventKind(row["family"]),
            claim_type=ClaimType(row["claim_type"]),
            status=ObservationStatus(row["status"]),
            stated=str(row["stated"]),
            value=_number(row.get("value")),
            unit=row.get("unit"),
            source=row.get("source"),
            source_observed_at=_time(row.get("source_observed_at")),
            refs=tuple(row.get("refs") or ()),
            corrects=row.get("corrects"),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None

    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None

    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
