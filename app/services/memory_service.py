from app.domain.event import Event
from app.domain.event_type import EventType
from app.domain.memory_event import MemoryEvent
from app.repositories.event_repository import EventRepository


class MemoryService:
    def __init__(self, repository: EventRepository) -> None:
        self._repository = repository

    def remember(self, memory: MemoryEvent) -> bool:
        if self._already_remembered(memory):
            return False

        self._repository.save(
            Event(
                timestamp=memory.timestamp,
                event_type=EventType.MEMORY_RECORDED,
                symbol=None,
                payload={
                    "memory_type": memory.event_type,
                    "subject": memory.subject,
                    "value": memory.value,
                },
            )
        )

        return True

    def history(self) -> list[MemoryEvent]:
        memories: list[MemoryEvent] = []

        for event in self._repository.load_all():
            if event.event_type != EventType.MEMORY_RECORDED:
                continue

            memories.append(
                MemoryEvent(
                    timestamp=event.timestamp,
                    event_type=str(event.payload["memory_type"]),
                    subject=str(event.payload["subject"]),
                    value=str(event.payload["value"]),
                )
            )

        return memories

    def _already_remembered(self, memory: MemoryEvent) -> bool:
        return any(
            existing.event_type == memory.event_type
            and existing.subject == memory.subject
            and existing.value == memory.value
            for existing in self.history()
        )
