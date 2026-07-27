from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from app.domain.daily_snapshot import DailySnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.memory.snapshot_repository import SnapshotRepository


class JsonSnapshotRepository(SnapshotRepository):
    def __init__(
        self,
        directory: Path = Path("data/portfolio_snapshots"),
    ) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def save(self, snapshot: DailySnapshot) -> None:
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
