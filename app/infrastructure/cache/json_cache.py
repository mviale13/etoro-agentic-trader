"""A small disk-backed cache for evidence that was already fetched."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

UNSAFE = re.compile(r"[^A-Za-z0-9._-]")


@dataclass(frozen=True, slots=True)
class CachedEntry:
    """A value that was observed once, and when."""

    value: dict[str, Any]
    stored_at: datetime

    def is_fresh(self, ttl: timedelta) -> bool:
        return datetime.now(UTC) - self.stored_at < ttl

    def is_from_today(self) -> bool:
        """True when the value was observed on the current UTC date."""

        return self.stored_at.date() == datetime.now(UTC).date()


class JsonCache:
    """
    Remember what a provider already told us.

    The cache never invents a value and never hides its age: a reader gets
    the stored value together with the moment it was observed, and decides
    for itself whether that is recent enough to use.

    A corrupt or unreadable entry is treated as absent rather than repaired,
    because a guessed cache entry would be indistinguishable from evidence.
    """

    def __init__(
        self,
        directory: Path | str = "data/cache",
    ) -> None:
        self.directory = Path(directory)

    def read(
        self,
        key: str,
    ) -> CachedEntry | None:
        """Return the stored entry, however old, or None."""

        path = self._path_for(key)

        if not path.exists():
            return None

        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            stored_at = datetime.fromisoformat(str(record["stored_at"]))
            value = record["value"]
        except (OSError, ValueError, KeyError, TypeError):
            return None

        if not isinstance(value, dict):
            return None

        if stored_at.tzinfo is None:
            stored_at = stored_at.replace(tzinfo=UTC)

        return CachedEntry(
            value=value,
            stored_at=stored_at,
        )

    def write(
        self,
        key: str,
        value: dict[str, Any],
    ) -> None:
        """Store a value observed now."""

        self.directory.mkdir(parents=True, exist_ok=True)

        self._path_for(key).write_text(
            json.dumps(
                {
                    "stored_at": datetime.now(UTC).isoformat(),
                    "value": value,
                },
                indent=2,
                sort_keys=True,
                default=str,
            ),
            encoding="utf-8",
        )

    def _path_for(
        self,
        key: str,
    ) -> Path:
        # Symbols carry characters a filename cannot ( ^VIX, CL=F, BRK/B ),
        # so the readable part is sanitised and a digest keeps it unique.
        readable = UNSAFE.sub("_", key)[:40]
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]

        return self.directory / f"{readable}.{digest}.json"
