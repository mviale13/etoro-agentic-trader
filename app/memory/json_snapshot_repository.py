from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.domain.daily_snapshot import DailySnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.infrastructure.evidence_root import evidence_path
from app.memory.snapshot_repository import SnapshotRepository


class JsonSnapshotRepository(SnapshotRepository):
    def __init__(
        self,
        directory: Path | str | None = None,
    ) -> None:
        # The evidence root, resolved at construction (#118, BQ10).
        # This one also *creates* its directory below, so a frozen
        # default made merely constructing it write into the
        # developer's tree — the second half of #118's finding.
        self._directory = (
            Path(directory)
            if directory is not None
            else evidence_path("portfolio_snapshots")
        )

    def save(self, snapshot: DailySnapshot) -> None:
        # Created when something is written, never merely by being
        # constructed: a repository that makes its directory in
        # `__init__` writes into the developer's tree the moment a test
        # instantiates it, which is the half of #118 that was about
        # writing rather than reading.
        self._directory.mkdir(parents=True, exist_ok=True)

        path = self._directory / f"{snapshot.date.isoformat()}.json"

        payload = asdict(snapshot)
        payload["date"] = snapshot.date.isoformat()

        path.write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def latest(self) -> DailySnapshot | None:
        files = sorted(self._directory.glob("*.json"))

        if not files:
            return None

        return self._load(files[-1])

    def previous(self) -> DailySnapshot | None:
        files = sorted(self._directory.glob("*.json"))

        if len(files) < 2:
            return None

        return self._load(files[-2])

    def history(self) -> list[DailySnapshot]:
        return [self._load(path) for path in sorted(self._directory.glob("*.json"))]

    def _load(self, path: Path) -> DailySnapshot:
        data = json.loads(path.read_text(encoding="utf-8"))

        allocation = Allocation(**data["portfolio"]["allocation"])

        portfolio = PortfolioSnapshot(
            allocation=allocation,
            total_value=data["portfolio"]["total_value"],
            positions=data["portfolio"]["positions"],
            largest_position=data["portfolio"]["largest_position"],
            largest_position_pct=data["portfolio"]["largest_position_pct"],
            risk_flags=tuple(data["portfolio"]["risk_flags"]),
        )

        return DailySnapshot(
            date=date.fromisoformat(data["date"]),
            portfolio=portfolio,
        )
