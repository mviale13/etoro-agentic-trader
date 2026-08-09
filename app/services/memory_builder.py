from datetime import UTC, datetime

from app.domain.memory_event import MemoryEvent
from app.domain.signal import Signal


class MemoryBuilder:
    def build(self, signals: list[Signal]) -> list[MemoryEvent]:
        memories: list[MemoryEvent] = []

        for signal in signals:
            if signal.type == "cash" and signal.title == "High Cash Position":
                memories.append(
                    MemoryEvent(
                        # Aware, like every other timestamp this platform
                        # writes. A naive one cannot be compared with them,
                        # and the journal sorts what it loads — so this one
                        # `datetime.now()` broke every page built on the
                        # Brain, permanently, from the moment it was saved.
                        timestamp=datetime.now(UTC),
                        event_type="portfolio_pattern",
                        subject="cash_allocation",
                        value="You tend to keep a high cash allocation.",
                    )
                )

        return memories
