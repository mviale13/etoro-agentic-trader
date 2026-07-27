from abc import ABC, abstractmethod

from app.domain.daily_snapshot import DailySnapshot


class SnapshotRepository(ABC):
    @abstractmethod
    def save(self, snapshot: DailySnapshot) -> None: ...

    @abstractmethod
    def latest(self) -> DailySnapshot | None: ...

    @abstractmethod
    def previous(self) -> DailySnapshot | None: ...

    @abstractmethod
    def history(self) -> list[DailySnapshot]: ...
