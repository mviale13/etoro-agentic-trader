from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class SnapshotReference:
    broker: str
    environment: str
    endpoint: str
    captured_at: datetime
    content_hash: str
    path: Path


@dataclass(frozen=True, slots=True)
class StoredSnapshot:
    """One capture read back out of the archive, exactly as it was written."""

    reference: SnapshotReference
    payload: Any
    metadata: JsonObject


class VersionedSnapshotStore:
    """
    Immutable filesystem store for raw evidence.

    The store preserves the complete payload exactly as supplied by the
    integration that captured it, wrapped with capture metadata.

    Existing snapshots are never overwritten.

    Captures were write-only until now, which made the archive a record
    nothing could consult: an eToro response could be audited by hand but
    never compared with the one before it. `recent` reads the newest
    captures back so a caller can say what changed, without a second
    archive being invented to hold the same evidence twice.
    """

    def __init__(self, root: Path | str = "data/evidence") -> None:
        self._root = Path(root)

    def save(
        self,
        *,
        broker: str,
        environment: str,
        endpoint: str,
        payload: Any,
        captured_at: datetime | None = None,
        metadata: JsonObject | None = None,
    ) -> SnapshotReference:
        timestamp = self._as_utc(captured_at or datetime.now(UTC))

        normalized_broker = self._safe_segment(broker)
        normalized_environment = self._safe_segment(environment)
        normalized_endpoint = self._safe_segment(endpoint)

        content_hash = self.content_hash(payload)

        directory = (
            self._root
            / normalized_broker
            / normalized_environment
            / normalized_endpoint
            / timestamp.strftime("%Y")
            / timestamp.strftime("%m")
            / timestamp.strftime("%d")
        )
        directory.mkdir(parents=True, exist_ok=True)

        timestamp_part = timestamp.strftime("%Y%m%dT%H%M%S.%fZ")
        filename = f"{timestamp_part}_{content_hash[:12]}.json"
        destination = directory / filename

        envelope: JsonObject = {
            "schema_version": 1,
            "broker": broker,
            "environment": environment,
            "endpoint": endpoint,
            "captured_at": timestamp.isoformat().replace("+00:00", "Z"),
            "content_hash": content_hash,
            "metadata": metadata or {},
            "payload": payload,
        }

        self._write_immutable_json(destination=destination, document=envelope)

        return SnapshotReference(
            broker=broker,
            environment=environment,
            endpoint=endpoint,
            captured_at=timestamp,
            content_hash=content_hash,
            path=destination,
        )

    def recent(
        self,
        *,
        broker: str,
        environment: str,
        endpoint: str,
        limit: int = 1,
        now: datetime | None = None,
    ) -> tuple[StoredSnapshot, ...]:
        """
        The most recent captures for one endpoint, newest first.

        An endpoint nothing has captured yet returns nothing, which is not
        an error: an archive with no history says so rather than inventing
        a first entry to compare against.

        The walk descends the dated directories newest first and stops as
        soon as `limit` captures have been read, so asking for the last two
        market observations does not open a year of eToro responses. File
        names begin with a fixed-width UTC timestamp, so their lexical
        order is their chronological order.

        `now` bounds the walk to captures at or before that moment; it is
        for reading history as of a point in time, and defaults to reading
        everything.
        """

        if limit <= 0:
            return ()

        directory = (
            self._root
            / self._safe_segment(broker)
            / self._safe_segment(environment)
            / self._safe_segment(endpoint)
        )

        if not directory.is_dir():
            return ()

        collected: list[StoredSnapshot] = []

        for day in self._days_newest_first(directory):
            for path in sorted(day.glob("*.json"), reverse=True):
                if path.name.startswith("."):
                    continue

                stored = self._read(path)

                if stored is None:
                    continue

                if now is not None and stored.reference.captured_at > now:
                    continue

                collected.append(stored)

                if len(collected) >= limit:
                    return tuple(collected)

        return tuple(collected)

    @staticmethod
    def _days_newest_first(directory: Path) -> Iterator[Path]:
        """Walk the year/month/day directories, newest first."""

        def descend(parent: Path) -> list[Path]:
            return sorted(
                (child for child in parent.iterdir() if child.is_dir()),
                key=lambda child: child.name,
                reverse=True,
            )

        for year in descend(directory):
            for month in descend(year):
                yield from descend(month)

    def _read(self, path: Path) -> StoredSnapshot | None:
        """
        One capture, or nothing when the file is not a readable envelope.

        A half-written or hand-edited file is skipped rather than raised
        on. The archive is evidence; one unreadable entry must not make the
        rest of it unreachable.
        """

        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

        if not isinstance(document, dict):
            return None

        try:
            captured_at = datetime.fromisoformat(
                str(document["captured_at"]).replace("Z", "+00:00"),
            )
        except (KeyError, ValueError):
            return None

        metadata = document.get("metadata")

        return StoredSnapshot(
            reference=SnapshotReference(
                broker=str(document.get("broker", "")),
                environment=str(document.get("environment", "")),
                endpoint=str(document.get("endpoint", "")),
                captured_at=self._as_utc(captured_at),
                content_hash=str(document.get("content_hash", "")),
                path=path,
            ),
            payload=document.get("payload"),
            metadata=metadata if isinstance(metadata, dict) else {},
        )

    @classmethod
    def content_hash(cls, payload: Any) -> str:
        """
        What this payload hashes to, under the store's own canonical form.

        Public because a caller deciding whether a capture is new must ask
        that question the same way the store answers it. Two hashing rules
        for one archive would disagree on exactly the payloads that matter.
        """

        return hashlib.sha256(
            cls._canonical_json(payload).encode("utf-8"),
        ).hexdigest()

    @staticmethod
    def _canonical_json(payload: Any) -> str:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)

    @staticmethod
    def _safe_segment(value: str) -> str:
        normalized = value.strip().lower().replace(" ", "_")

        if not normalized:
            raise ValueError("Snapshot path segment cannot be empty.")

        allowed = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")
        sanitized = "".join(
            character for character in normalized if character in allowed
        )

        if not sanitized:
            raise ValueError(f"Invalid snapshot path segment: {value!r}")

        return sanitized

    @staticmethod
    def _write_immutable_json(*, destination: Path, document: JsonObject) -> None:
        if destination.exists():
            raise FileExistsError(f"Snapshot already exists: {destination}")

        temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")

        try:
            with temporary.open("x", encoding="utf-8") as file:
                json.dump(
                    document,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                    default=str,
                )
                file.write("\n")
                file.flush()
                os.fsync(file.fileno())

            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
