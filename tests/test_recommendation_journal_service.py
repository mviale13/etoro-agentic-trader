from datetime import UTC, datetime
from pathlib import Path

from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.json_event_repository import JsonEventRepository
from app.services.recommendation_journal_service import (
    RecommendationJournalService,
)


def test_journal(tmp_path: Path) -> None:
    repository = JsonEventRepository(tmp_path)

    repository.save(
        Event(
            timestamp=datetime.now(UTC),
            event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
            symbol="MSFT",
            payload={
                "recommendation": "BUY",
                "successful": True,
            },
        )
    )

    entries = RecommendationJournalService(
        repository,
    ).entries()

    assert len(entries) == 1
    assert entries[0].symbol == "MSFT"
    assert entries[0].recommendation == "BUY"
    assert entries[0].successful is True
    assert entries[0].reflection == "Successful recommendation."
