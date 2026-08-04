from app.domain.recommendation_journal_entry import (
    RecommendationJournalEntry,
)
from app.repositories.event_repository import EventRepository


class RecommendationJournalService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def entries(
        self,
    ) -> list[RecommendationJournalEntry]:
        journal: list[RecommendationJournalEntry] = []

        for event in self._repository.load_all():
            if event.event_type != "recommendation_outcome_recorded":
                continue

            journal.append(
                RecommendationJournalEntry(
                    timestamp=event.timestamp,
                    symbol=event.symbol or "",
                    recommendation=str(
                        event.payload.get(
                            "recommendation",
                            "",
                        )
                    ),
                    successful=bool(
                        event.payload.get(
                            "successful",
                            False,
                        )
                    ),
                    reflection=(
                        "Successful recommendation."
                        if event.payload.get("successful")
                        else "Recommendation should be reviewed."
                    ),
                )
            )

        return journal
