from datetime import datetime

from app.domain.memory_event import MemoryEvent
from app.services.pattern_engine import PatternEngine


def test_detects_recurring_cash_pattern() -> None:
    memories = [
        MemoryEvent(
            timestamp=datetime.now(),
            event_type="portfolio_pattern",
            subject="cash_allocation",
            value="High cash.",
        )
        for _ in range(3)
    ]

    patterns = PatternEngine().analyze(memories)

    assert len(patterns) == 1
    assert patterns[0].confidence == 90


def test_no_pattern_with_insufficient_history() -> None:
    memories = [
        MemoryEvent(
            timestamp=datetime.now(),
            event_type="portfolio_pattern",
            subject="cash_allocation",
            value="High cash.",
        )
        for _ in range(2)
    ]

    assert PatternEngine().analyze(memories) == []
