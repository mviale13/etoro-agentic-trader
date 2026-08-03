import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.infrastructure.evidence.versioned_snapshot_store import (
    VersionedSnapshotStore,
)


def test_saves_complete_versioned_snapshot(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)
    captured_at = datetime(2026, 7, 30, 15, 30, 12, 123456, tzinfo=UTC)

    payload = {
        "positions": [
            {
                "instrumentId": 42,
                "amount": 1250.5,
                "unrealizedPnL": {"pnL": 18.2},
            }
        ],
        "orders": [],
    }

    reference = store.save(
        broker="eToro",
        environment="demo",
        endpoint="account",
        payload=payload,
        captured_at=captured_at,
        metadata={
            "latency_ms": 187.4,
            "http_status": 200,
        },
    )

    assert reference.path.exists()
    assert reference.path.parent == (
        tmp_path / "etoro" / "demo" / "account" / "2026" / "07" / "30"
    )

    stored = json.loads(reference.path.read_text(encoding="utf-8"))

    assert stored["schema_version"] == 1
    assert stored["broker"] == "eToro"
    assert stored["environment"] == "demo"
    assert stored["endpoint"] == "account"
    assert stored["captured_at"] == "2026-07-30T15:30:12.123456Z"
    assert stored["metadata"]["latency_ms"] == 187.4
    assert stored["payload"] == payload
    assert stored["content_hash"] == reference.content_hash


def test_creates_a_new_version_for_each_capture(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)
    payload = {"equity": 100_000}

    first = store.save(
        broker="etoro",
        environment="demo",
        endpoint="account",
        payload=payload,
        captured_at=datetime(2026, 7, 30, 15, 0, tzinfo=UTC),
    )
    second = store.save(
        broker="etoro",
        environment="demo",
        endpoint="account",
        payload=payload,
        captured_at=datetime(2026, 7, 30, 16, 0, tzinfo=UTC),
    )

    assert first.path != second.path
    assert first.content_hash == second.content_hash
    assert first.path.exists()
    assert second.path.exists()


def capture(
    store: VersionedSnapshotStore,
    payload: dict[str, object],
    captured_at: datetime,
) -> None:
    store.save(
        broker="etoro",
        environment="demo",
        endpoint="account",
        payload=payload,
        captured_at=captured_at,
    )


def recent(
    store: VersionedSnapshotStore,
    limit: int = 1,
    now: datetime | None = None,
) -> tuple[object, ...]:
    return store.recent(
        broker="etoro",
        environment="demo",
        endpoint="account",
        limit=limit,
        now=now,
    )


def test_an_endpoint_nothing_captured_reports_no_history(tmp_path: Path) -> None:
    """Not an error. An archive with no history says so."""

    assert recent(VersionedSnapshotStore(root=tmp_path)) == ()


def test_reads_captures_back_newest_first(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)

    for day, equity in ((28, 100), (30, 300), (29, 200)):
        capture(
            store,
            {"equity": equity},
            datetime(2026, 7, day, 15, 0, tzinfo=UTC),
        )

    stored = store.recent(
        broker="etoro",
        environment="demo",
        endpoint="account",
        limit=2,
    )

    assert [item.payload["equity"] for item in stored] == [300, 200]
    assert stored[0].reference.captured_at == datetime(
        2026, 7, 30, 15, 0, tzinfo=UTC
    )
    assert stored[0].reference.endpoint == "account"
    assert stored[0].reference.content_hash == store.content_hash({"equity": 300})


def test_reads_back_across_years(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)

    capture(store, {"equity": 1}, datetime(2025, 12, 31, 23, 0, tzinfo=UTC))
    capture(store, {"equity": 2}, datetime(2026, 1, 1, 1, 0, tzinfo=UTC))

    stored = store.recent(
        broker="etoro",
        environment="demo",
        endpoint="account",
        limit=5,
    )

    assert [item.payload["equity"] for item in stored] == [2, 1]


def test_history_can_be_read_as_of_a_moment(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)

    capture(store, {"equity": 1}, datetime(2026, 7, 28, 15, 0, tzinfo=UTC))
    capture(store, {"equity": 2}, datetime(2026, 7, 30, 15, 0, tzinfo=UTC))

    stored = store.recent(
        broker="etoro",
        environment="demo",
        endpoint="account",
        limit=5,
        now=datetime(2026, 7, 29, 0, 0, tzinfo=UTC),
    )

    assert [item.payload["equity"] for item in stored] == [1]


def test_an_unreadable_capture_does_not_hide_the_rest(tmp_path: Path) -> None:
    """
    One corrupt entry must not make the archive unreachable.

    The archive is evidence. A half-written file is skipped, and what was
    written properly is still returned.
    """

    store = VersionedSnapshotStore(root=tmp_path)

    capture(store, {"equity": 1}, datetime(2026, 7, 28, 15, 0, tzinfo=UTC))

    directory = tmp_path / "etoro" / "demo" / "account" / "2026" / "07" / "28"
    (directory / "20260730T150000.000000Z_deadbeefcafe.json").write_text(
        "{ not json",
        encoding="utf-8",
    )

    stored = store.recent(
        broker="etoro",
        environment="demo",
        endpoint="account",
        limit=5,
    )

    assert [item.payload["equity"] for item in stored] == [1]


def test_asking_for_no_history_reads_nothing(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)

    capture(store, {"equity": 1}, datetime(2026, 7, 28, 15, 0, tzinfo=UTC))

    assert recent(store, limit=0) == ()


def test_rejects_empty_path_segments(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)

    with pytest.raises(ValueError):
        store.save(
            broker="",
            environment="demo",
            endpoint="account",
            payload={},
        )
