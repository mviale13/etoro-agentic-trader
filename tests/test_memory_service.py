from datetime import UTC, datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.memory_event import MemoryEvent
from app.repositories.json_event_repository import JsonEventRepository
from app.services.memory_service import MemoryService


def test_remember_persists_memory(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    service = MemoryService(repository)

    memory = MemoryEvent(
        timestamp=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
        event_type="portfolio_pattern",
        subject="cash_allocation",
        value="Investor frequently maintains a high cash allocation.",
    )

    saved = service.remember(memory)

    assert saved is True
    assert service.history() == [memory]


def test_remember_ignores_duplicate_memory(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)
    service = MemoryService(repository)

    first = MemoryEvent(
        timestamp=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
        event_type="portfolio_pattern",
        subject="cash_allocation",
        value="Investor frequently maintains a high cash allocation.",
    )
    duplicate = MemoryEvent(
        timestamp=datetime(2026, 7, 28, 9, 0, tzinfo=UTC),
        event_type="portfolio_pattern",
        subject="cash_allocation",
        value="Investor frequently maintains a high cash allocation.",
    )

    assert service.remember(first) is True
    assert service.remember(duplicate) is False
    assert service.history() == [first]


def test_history_ignores_non_memory_events(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
            event_type="portfolio_analyzed",
            symbol=None,
            payload={},
        )
    )

    service = MemoryService(repository)

    assert service.history() == []


def test_history_returns_memories_in_chronological_order(
    tmp_path: Path,
) -> None:
    repository = JsonEventRepository(tmp_path)
    service = MemoryService(repository)

    first = MemoryEvent(
        timestamp=datetime(2026, 7, 27, 8, 0, tzinfo=UTC),
        event_type="portfolio_pattern",
        subject="cash_allocation",
        value="Cash allocation remained high.",
    )
    second = MemoryEvent(
        timestamp=datetime(2026, 7, 27, 9, 0, tzinfo=UTC),
        event_type="portfolio_pattern",
        subject="diversification",
        value="Portfolio diversification improved.",
    )

    service.remember(second)
    service.remember(first)

    assert service.history() == [first, second]
