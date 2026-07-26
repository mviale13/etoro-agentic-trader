from abc import ABC, abstractmethod

from app.domain.event import Event


class EventRepository(ABC):
    @abstractmethod
    def save(self, event: Event) -> None: ...

    @abstractmethod
    def load_all(self) -> list[Event]: ...

    @abstractmethod
    def load_latest(self, limit: int = 1) -> list[Event]: ...
