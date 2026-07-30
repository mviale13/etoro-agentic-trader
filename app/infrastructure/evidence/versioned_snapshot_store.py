from __future__ import annotations

import hashlib
import json
import os
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


class VersionedSnapshotStore:
    """
    Immutable filesystem store for raw broker evidence.

    The store preserves the complete payload exactly as supplied by the broker
    integration, wrapped with capture metadata.

    Existing snapshots are never overwritten.
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

        payload_json = self._canonical_json(payload)
        content_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

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
