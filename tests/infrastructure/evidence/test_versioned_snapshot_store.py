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


def test_rejects_empty_path_segments(tmp_path: Path) -> None:
    store = VersionedSnapshotStore(root=tmp_path)

    with pytest.raises(ValueError):
        store.save(
            broker="",
            environment="demo",
            endpoint="account",
            payload={},
        )
