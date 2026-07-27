from app.domain.memory_event import MemoryEvent
from app.domain.pattern import Pattern


class PatternEngine:
    def analyze(
        self,
        memories: list[MemoryEvent],
    ) -> list[Pattern]:
        cash_memories = [
            memory for memory in memories if memory.subject == "cash_allocation"
        ]

        patterns: list[Pattern] = []

        if len(cash_memories) >= 3:
            patterns.append(
                Pattern(
                    title="Recurring Cash Strategy",
                    description=("You consistently maintain a high cash allocation."),
                    confidence=90,
                )
            )

        return patterns
