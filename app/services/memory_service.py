from app.domain.memory_event import MemoryEvent


class MemoryService:
    def __init__(self) -> None:
        self._events: list[MemoryEvent] = []

    def remember(self, event: MemoryEvent) -> None:
        self._events.append(event)

    def history(self) -> list[MemoryEvent]:
        return list(self._events)
