"""S5.2a: a record written under one schema never decodes as another.

The defect was quiet, which is what makes it worth a suite of its own.
S5.1 added a field an establishment gate reads; records written hours
earlier decoded without it, every gate needing it failed, and the store
kept serving them until the daily expiry. Nothing errored, and a real
measurement looked like an evidence gap.

One test per invariant in the ruling's section 8.
"""

from __future__ import annotations

import json
import pathlib
from datetime import UTC, datetime, timedelta
from typing import Any

from app.infrastructure.cache.json_cache import (
    JsonCache,
    RecordCompatibility,
)


def _written(path: pathlib.Path, key: str) -> dict[str, Any]:
    """The record on disk, as a store's next reader would find it."""

    files = list(path.glob("*.json"))

    assert len(files) == 1, files

    return json.loads(files[0].read_text(encoding="utf-8"))


# ── 1: the current schema decodes ───────────────────────────────────


def test_a_record_at_the_current_schema_decodes(tmp_path: pathlib.Path) -> None:
    cache = JsonCache(tmp_path, schema=3)

    cache.write("BTC", {"emitted": 20_068_365})

    entry = cache.read("BTC")

    assert entry is not None
    assert entry.value == {"emitted": 20_068_365}
    assert entry.schema == 3
    assert entry.compatibility is RecordCompatibility.CURRENT

    # And the schema is stored beside the value, never inside it, so a
    # store's own payload shape is not constrained by bookkeeping.
    record = _written(tmp_path, "BTC")

    assert record["schema"] == 3
    assert "schema" not in record["value"]


# ── 2: an incompatible schema does not silently decode ──────────────


def test_an_older_schema_with_no_migration_is_a_miss(
    tmp_path: pathlib.Path,
) -> None:
    """The defect, as a rule.

    A version-1 record read by a version-2 reader is not a version-2
    record with a field missing. It is a cache miss.
    """

    JsonCache(tmp_path, schema=1).write("ADA", {"supply": 1})

    reader = JsonCache(tmp_path, schema=2)

    assert reader.read("ADA") is None

    # And the reader can tell an absent record from a rejected one,
    # which `read` deliberately cannot.
    rejected = reader.inspect("ADA")

    assert rejected is not None
    assert rejected.compatibility is RecordCompatibility.INCOMPATIBLE
    assert rejected.schema == 1

    assert reader.inspect("NEVER-WRITTEN") is None


def test_a_record_from_a_newer_schema_is_never_migrated_backwards(
    tmp_path: pathlib.Path,
) -> None:
    """Two processes on different versions share a directory more often
    than anyone plans for, and guessing which fields the newer one
    dropped is the guess this class refuses everywhere else."""

    JsonCache(tmp_path, schema=5).write("SOL", {"issuance": 0.037})

    reader = JsonCache(tmp_path, schema=2, migrations={1: lambda value: value})

    assert reader.read("SOL") is None

    seen = reader.inspect("SOL")

    assert seen is not None
    assert seen.compatibility is RecordCompatibility.INCOMPATIBLE


# ── 3: a migration works only when explicitly registered ────────────


def test_a_registered_migration_brings_a_record_forward(
    tmp_path: pathlib.Path,
) -> None:
    JsonCache(tmp_path, schema=1).write("ADA", {"supply": 1})

    def _rename(value: dict[str, Any]) -> dict[str, Any]:
        return {"emitted": value["supply"]}

    reader = JsonCache(tmp_path, schema=2, migrations={1: _rename})

    entry = reader.read("ADA")

    assert entry is not None
    assert entry.value == {"emitted": 1}
    assert entry.schema == 2
    assert entry.compatibility is RecordCompatibility.MIGRATED


def test_migrations_are_applied_in_sequence_and_a_gap_refuses(
    tmp_path: pathlib.Path,
) -> None:
    """A store missing any step cannot read the record at all — which is
    the honest answer, and the alternative is inventing the step."""

    JsonCache(tmp_path, schema=1).write("ADA", {"n": 1})

    chained = JsonCache(
        tmp_path,
        schema=3,
        migrations={
            1: lambda value: {"n": value["n"] + 1},
            2: lambda value: {"n": value["n"] + 1},
        },
    )

    entry = chained.read("ADA")

    assert entry is not None
    assert entry.value == {"n": 3}

    # Remove the middle step and the record stops being readable.
    gapped = JsonCache(
        tmp_path,
        schema=3,
        migrations={1: lambda value: {"n": value["n"] + 1}},
    )

    assert gapped.read("ADA") is None


def test_a_migration_may_refuse_one_record(tmp_path: pathlib.Path) -> None:
    """Returning None is how a migration says *this* record cannot come
    forward, without the store pretending every record can."""

    JsonCache(tmp_path, schema=1).write("GOOD", {"n": 1})
    JsonCache(tmp_path, schema=1).write("BAD", {"n": -1})

    def _positive(value: dict[str, Any]) -> dict[str, Any] | None:
        return value if value["n"] > 0 else None

    reader = JsonCache(tmp_path, schema=2, migrations={1: _positive})

    assert reader.read("GOOD") is not None
    assert reader.read("BAD") is None


# ── 4: malformed version metadata fails safely ──────────────────────


def test_version_metadata_that_is_not_a_version_is_malformed(
    tmp_path: pathlib.Path,
) -> None:
    """Reading `"schema": "two"` as unversioned would be exactly the
    permissive decode this class exists to stop."""

    tmp_path.mkdir(parents=True, exist_ok=True)

    cache = JsonCache(tmp_path, schema=2, accepts_unversioned=True)

    path = cache._path_for("ADA")  # noqa: SLF001 — writing a record by hand
    path.write_text(
        json.dumps(
            {
                "stored_at": datetime.now(UTC).isoformat(),
                "schema": "two",
                "value": {"supply": 1},
            }
        ),
        encoding="utf-8",
    )

    assert cache.read("ADA") is None

    seen = cache.inspect("ADA")

    assert seen is not None
    assert seen.compatibility is RecordCompatibility.MALFORMED


def test_an_unreadable_record_is_absent_rather_than_repaired(
    tmp_path: pathlib.Path,
) -> None:
    cache = JsonCache(tmp_path, schema=1)

    tmp_path.mkdir(parents=True, exist_ok=True)
    cache._path_for("ADA").write_text("{not json", encoding="utf-8")  # noqa: SLF001

    assert cache.read("ADA") is None
    assert cache.inspect("ADA") is None


# ── 5: pre-version records get an explicit treatment ────────────────


def test_unversioned_records_are_accepted_only_by_declaration(
    tmp_path: pathlib.Path,
) -> None:
    """Never an accident. A store either accepts records written before
    it declared a schema or it does not, and both are stated where the
    cache is built."""

    # Written the way every store wrote before S5.2a.
    JsonCache(tmp_path).write("ADA", {"supply": 1})

    record = _written(tmp_path, "ADA")

    assert "schema" not in record

    accepting = JsonCache(tmp_path, schema=1, accepts_unversioned=True)

    entry = accepting.read("ADA")

    assert entry is not None
    assert entry.compatibility is RecordCompatibility.UNVERSIONED
    assert entry.value == {"supply": 1}

    refusing = JsonCache(tmp_path, schema=1)

    assert refusing.read("ADA") is None
    assert refusing.inspect("ADA").compatibility is RecordCompatibility.INCOMPATIBLE  # type: ignore[union-attr]


def test_accepting_unversioned_does_not_survive_the_next_bump(
    tmp_path: pathlib.Path,
) -> None:
    """The protection the ten stores actually gain.

    Accepting pre-version records at schema 1 is a statement about
    schema 1. The moment a store moves to 2, those records need a
    migration or they re-acquire — so a shape cannot change by accident
    even in a store that has never versioned anything.
    """

    JsonCache(tmp_path).write("ADA", {"supply": 1})

    assert JsonCache(tmp_path, schema=1, accepts_unversioned=True).read("ADA")

    bumped = JsonCache(tmp_path, schema=2, accepts_unversioned=True)

    assert bumped.read("ADA") is None


# ── 6: acquisition behaviour is unchanged ───────────────────────────


def test_a_store_that_declares_no_schema_behaves_exactly_as_before(
    tmp_path: pathlib.Path,
) -> None:
    """The legacy contract, kept. A store that has never changed shape
    must not re-acquire because this class learned a new trick."""

    legacy = JsonCache(tmp_path)

    legacy.write("ADA", {"supply": 1})

    record = _written(tmp_path, "ADA")

    assert "schema" not in record

    entry = legacy.read("ADA")

    assert entry is not None
    assert entry.compatibility is RecordCompatibility.CURRENT
    assert entry.schema is None

    # Including a record some other reader stamped: an undeclared schema
    # asks no questions, which is what "unchanged" means.
    JsonCache(tmp_path, schema=9).write("ETH", {"supply": 2})

    assert legacy.read("ETH") is not None


def test_a_miss_re_acquires_under_the_existing_spend_rules(
    tmp_path: pathlib.Path,
) -> None:
    """A rejected record is a *cache* miss, so the store's own
    acquisition contract decides what happens — not this class.

    `stored()` is the read-only door and must stay silent; the
    acquiring door re-reads. Both are exercised against a store whose
    records were written under the previous schema.
    """

    from app.providers.primary_supply_provider import (
        SCHEMA,
        CachedPrimarySupplyProvider,
    )

    JsonCache(tmp_path, schema=SCHEMA - 1).write("ADA", {"facts": []})

    read_only = CachedPrimarySupplyProvider.stored(
        cache=JsonCache(tmp_path, schema=SCHEMA)
    )

    assert read_only.facts("ADA") == ()

    class _Exploding:
        @staticmethod
        def facts(symbol: str) -> tuple[()]:
            raise AssertionError("a read-only door acquired something")

    silent = CachedPrimarySupplyProvider(
        provider=_Exploding(),  # type: ignore[arg-type]
        cache=JsonCache(tmp_path, schema=SCHEMA),
        acquires=False,
    )

    assert silent.facts("ADA") == ()


# ── 7: the caches on disk behave intentionally ──────────────────────


def test_every_store_declares_what_it_does_with_pre_version_records() -> None:
    """No store is left deciding by accident.

    Ten stores accept their pre-version records deliberately, because
    those records are the shape schema 1 describes. `primary_supply`
    refuses its version-1 records deliberately, because they carry no
    provenance and the establishment gate reads provenance — there is
    nothing to bring forward.
    """

    import ast

    root = pathlib.Path(__file__).resolve().parent.parent

    declared: dict[str, bool] = {}

    for path in sorted((root / "app" / "providers").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            if not (isinstance(node.func, ast.Name) and node.func.id == "JsonCache"):
                continue

            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue

            store = str(node.args[0].value)

            if not store.startswith("data/cache/"):
                continue

            keywords = {kw.arg for kw in node.keywords}

            assert "schema" in keywords, store

            declared[store] = "accepts_unversioned" in keywords

    assert len(declared) == 12, sorted(declared)

    # Two stores refuse pre-version records, each for its own reason.
    # `primary_supply` had version-1 records carrying no provenance, and
    # the establishment gate reads provenance. `etf_flows` was created
    # after the contract existed, so it has no pre-version records at
    # all — accepting some would be a policy about a thing that cannot
    # happen.
    refusing = {"data/cache/primary_supply", "data/cache/etf_flows"}

    for store, accepts in declared.items():
        assert accepts is (store not in refusing), store


def test_records_on_disk_today_still_decode(tmp_path: pathlib.Path) -> None:
    """The ten stores must not have been made to re-acquire.

    Written the old way and read by the new declaration, a record is
    served — so adopting the contract cost no live API call.
    """

    JsonCache(tmp_path).write("AAPL", {"price": 1.0})

    served = JsonCache(tmp_path, schema=1, accepts_unversioned=True).read("AAPL")

    assert served is not None
    assert served.value == {"price": 1.0}
    assert served.is_from_today()
    assert served.is_fresh(timedelta(minutes=15))
