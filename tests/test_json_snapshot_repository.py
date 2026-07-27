from datetime import date

from app.domain.daily_snapshot import DailySnapshot
from app.domain.portfolio_snapshot import Allocation, PortfolioSnapshot
from app.memory.json_snapshot_repository import JsonSnapshotRepository


def make_snapshot(day: int) -> DailySnapshot:
    return DailySnapshot(
        date=date(2026, 7, day),
        portfolio=PortfolioSnapshot(
            total_value=100000,
            positions=10,
            allocation=Allocation(
                cash=20,
                stocks=70,
                etfs=10,
                crypto=0,
                unclassified=0,
            ),
            largest_position="NVDA",
            largest_position_pct=12,
            risk_flags=(),
        ),
    )


def test_save_and_latest(tmp_path) -> None:
    repository = JsonSnapshotRepository(tmp_path)

    snapshot = make_snapshot(27)
    repository.save(snapshot)

    latest = repository.latest()

    assert latest is not None
    assert latest.date == snapshot.date


def test_previous_snapshot(tmp_path) -> None:
    repository = JsonSnapshotRepository(tmp_path)

    repository.save(make_snapshot(27))
    repository.save(make_snapshot(28))

    previous = repository.previous()

    assert previous is not None
    assert previous.date.day == 27


def test_history_returns_all_snapshots(tmp_path) -> None:
    repository = JsonSnapshotRepository(tmp_path)

    repository.save(make_snapshot(27))
    repository.save(make_snapshot(28))
    repository.save(make_snapshot(29))

    history = repository.history()

    assert len(history) == 3
    assert history[-1].date.day == 29
