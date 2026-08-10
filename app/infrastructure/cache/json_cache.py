"""A small disk-backed cache for evidence that was already fetched.

**A record written under one schema must never decode as though it
belonged to another.** That is the contract this module owns, and it
owns it rather than each provider repeating it: eleven copies of four
lines means the eleventh is the one that gets forgotten, which is
exactly how the defect that prompted this arose.

The failure it prevents is quiet. S5.1 added a `provenance` field that
an establishment gate reads; records written hours earlier decoded
without it, every gate needing it failed, and the store went on serving
those records until the daily expiry. Nothing errored. A real
measurement looked like an evidence gap.

```text
CURRENT       the schema this reader asked for        → decode
MIGRATED      an older schema with a registered path  → migrate, decode
UNVERSIONED   written before the store declared one   → by declared policy
INCOMPATIBLE  a different schema, no migration        → cache miss
MALFORMED     unreadable, or version metadata is junk → cache miss
```

A miss is a *cache* miss. It re-acquires under the store's existing
spend rules and destroys nothing: this class writes only under
`data/cache/`, and the authoritative evidence stores — knowledge,
statements, decisions, events, evidence snapshots — are different
classes with different contracts. Losing a cached materialisation of a
provider response is not losing provenance.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any

UNSAFE = re.compile(r"[^A-Za-z0-9._-]")

#: The key a record's schema is stored under, beside the value rather
#: than inside it — so a store's own payload shape is never constrained
#: by the cache's bookkeeping.
SCHEMA_KEY = "schema"


class RecordCompatibility(StrEnum):
    """What a stored record is to the reader that asked for it."""

    #: Written under the schema this reader declares.
    CURRENT = "current"

    #: Written under an older schema, brought forward by a migration the
    #: store registered by name.
    MIGRATED = "migrated"

    #: Written before this store declared a schema at all. Never an
    #: accident: a store either accepts these deliberately or it does
    #: not, and both are stated at construction.
    UNVERSIONED = "unversioned"

    #: A schema this reader does not know and cannot migrate from.
    INCOMPATIBLE = "incompatible"

    #: Not readable as a record, or its version metadata is not a
    #: version. Rejected rather than guessed at.
    MALFORMED = "malformed"

    @property
    def is_usable(self) -> bool:
        return self in (
            RecordCompatibility.CURRENT,
            RecordCompatibility.MIGRATED,
            RecordCompatibility.UNVERSIONED,
        )


#: A migration takes a record's value under the older schema and returns
#: it under the next one. It may return None to refuse, which is how a
#: migration says "this particular record cannot come forward" without
#: the store having to pretend it can.
Migration = Callable[[dict[str, Any]], dict[str, Any] | None]


@dataclass(frozen=True, slots=True)
class CachedEntry:
    """A value that was observed once, and when."""

    value: dict[str, Any]
    stored_at: datetime

    #: The schema the record was written under. None where the store
    #: declares no schema, or the record predates the store declaring
    #: one.
    schema: int | None = None

    #: How the record reached this reader. `CURRENT` for every store
    #: that declares no schema, which is the contract those stores had
    #: before and keeps them unchanged.
    compatibility: RecordCompatibility = RecordCompatibility.CURRENT

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
    A record of the wrong *shape* is treated the same way, and for the same
    reason — a half-decoded record is a guess with better manners.
    """

    def __init__(
        self,
        directory: Path | str = "data/cache",
        schema: int | None = None,
        migrations: Mapping[int, Migration] | None = None,
        accepts_unversioned: bool = False,
    ) -> None:
        """
        `schema` is the shape this reader understands. Omitted, the cache
        behaves exactly as it did before schemas existed — every readable
        record is `CURRENT` — which is what keeps a store that has never
        changed shape from re-acquiring for no reason.

        `migrations` maps *from* an older schema to a function producing
        the next one. They are applied in sequence, so a store at 3 with
        migrations for 1 and 2 can read a version-1 record.

        `accepts_unversioned` states what to do with records written
        before this store declared a schema. It is a decision, not a
        default: a store that says True is asserting those records have
        the shape its first schema describes, and one that says False
        will re-acquire them.
        """

        self.directory = Path(directory)
        self.schema = schema
        self.migrations: Mapping[int, Migration] = migrations or {}
        self.accepts_unversioned = accepts_unversioned

    def read(
        self,
        key: str,
    ) -> CachedEntry | None:
        """The stored entry, however old, or None where none is usable."""

        entry = self.inspect(key)

        if entry is None or not entry.compatibility.is_usable:
            return None

        return entry

    def inspect(
        self,
        key: str,
    ) -> CachedEntry | None:
        """The stored entry *with* its verdict, usable or not.

        `read` is the door a provider uses and drops anything unusable.
        This one exists so a store — or a test — can tell an absent
        record from one that was rejected, which `read` deliberately
        cannot.
        """

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

        found = record.get(SCHEMA_KEY)

        # Version metadata that is not a version is malformed, not
        # absent. Reading `"schema": "two"` as unversioned would be the
        # permissive decode this class exists to stop.
        if found is not None and not isinstance(found, int):
            return CachedEntry(
                value=value,
                stored_at=stored_at,
                schema=None,
                compatibility=RecordCompatibility.MALFORMED,
            )

        if self.schema is None:
            # A store that declares no schema keeps the contract it had.
            return CachedEntry(value=value, stored_at=stored_at, schema=found)

        return self._reconcile(value, stored_at, found)

    def write(
        self,
        key: str,
        value: dict[str, Any],
    ) -> None:
        """Store a value observed now, stamped with this reader's schema."""

        self.directory.mkdir(parents=True, exist_ok=True)

        record: dict[str, Any] = {
            "stored_at": datetime.now(UTC).isoformat(),
            "value": value,
        }

        if self.schema is not None:
            record[SCHEMA_KEY] = self.schema

        self._path_for(key).write_text(
            json.dumps(record, indent=2, sort_keys=True, default=str),
            encoding="utf-8",
        )

    # ── the contract ────────────────────────────────────────────────

    def _reconcile(
        self,
        value: dict[str, Any],
        stored_at: datetime,
        found: int | None,
    ) -> CachedEntry:
        assert self.schema is not None

        if found == self.schema:
            return CachedEntry(
                value=value,
                stored_at=stored_at,
                schema=found,
                compatibility=RecordCompatibility.CURRENT,
            )

        if found is None:
            if not self.accepts_unversioned:
                return CachedEntry(
                    value=value,
                    stored_at=stored_at,
                    schema=None,
                    compatibility=RecordCompatibility.INCOMPATIBLE,
                )

            # Accepting a pre-version record means asserting it has the
            # shape schema 1 describes — nothing more. It then faces the
            # same migration chain an explicit version-1 record would,
            # which is the whole protection: a store on schema 1 today
            # reads its old records, and the moment it moves to 2 those
            # records need a migration like everything else.
            #
            # Written after the first attempt let `accepts_unversioned`
            # wave records through at any schema, which would have
            # rebuilt the silent decode this class exists to stop.
            if self.schema == 1:
                return CachedEntry(
                    value=value,
                    stored_at=stored_at,
                    schema=None,
                    compatibility=RecordCompatibility.UNVERSIONED,
                )

            found = 1

        # A record from the future is never migrated backwards. Two
        # processes on different versions share a directory more often
        # than anyone plans for, and guessing which fields the newer one
        # dropped is the same guess this class refuses everywhere else.
        if found > self.schema:
            return CachedEntry(
                value=value,
                stored_at=stored_at,
                schema=found,
                compatibility=RecordCompatibility.INCOMPATIBLE,
            )

        migrated = self._migrate(value, found)

        if migrated is None:
            return CachedEntry(
                value=value,
                stored_at=stored_at,
                schema=found,
                compatibility=RecordCompatibility.INCOMPATIBLE,
            )

        return CachedEntry(
            value=migrated,
            stored_at=stored_at,
            schema=self.schema,
            compatibility=RecordCompatibility.MIGRATED,
        )

    def _migrate(
        self,
        value: dict[str, Any],
        found: int,
    ) -> dict[str, Any] | None:
        """Step a record forward one schema at a time, or refuse.

        Sequential and explicit. A store missing any step in the chain
        cannot read the record at all — which is the honest answer, and
        the alternative is inventing the missing step.
        """

        assert self.schema is not None

        current = value

        for version in range(found, self.schema):
            migration = self.migrations.get(version)

            if migration is None:
                return None

            stepped = migration(current)

            if stepped is None:
                return None

            current = stepped

        return current

    def _path_for(
        self,
        key: str,
    ) -> Path:
        # Symbols carry characters a filename cannot ( ^VIX, CL=F, BRK/B ),
        # so the readable part is sanitised and a digest keeps it unique.
        readable = UNSAFE.sub("_", key)[:40]
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]

        return self.directory / f"{readable}.{digest}.json"
