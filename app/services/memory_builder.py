from datetime import datetime

from app.domain.memory_event import MemoryEvent
from app.domain.signal import Signal


class MemoryBuilder:
    def build(self, signals: list[Signal]) -> list[MemoryEvent]:
        memories: list[MemoryEvent] = []

        for signal in signals:
            if signal.type == "cash" and signal.title == "High Cash Position":
                memories.append(
                    MemoryEvent(
                        timestamp=datetime.now(),
                        event_type="portfolio_pattern",
                        subject="cash_allocation",
                        value="You tend to keep a high cash allocation.",
                    )
                )

        return memories
