from datetime import datetime

from app.domain.committee_outcome import (
    CommitteeOutcome,
    is_recommendation_successful,
)
from app.domain.event import Event
from app.domain.event_type import EventType
from app.repositories.event_repository import EventRepository


class CommitteeOutcomeService:
    def __init__(
        self,
        repository: EventRepository,
    ) -> None:
        self._repository = repository

    def record(
        self,
        *,
        recommendation_timestamp: datetime,
        evaluation_timestamp: datetime,
        symbol: str,
        recommendation: str,
        entry_price: float,
        evaluation_price: float,
    ) -> CommitteeOutcome:
        if entry_price <= 0:
            raise ValueError("Entry price must be greater than zero.")

        normalized_recommendation = recommendation.upper().strip()

        return_pct = round(
            ((evaluation_price - entry_price) / entry_price) * 100,
            2,
        )

        successful = is_recommendation_successful(
            normalized_recommendation,
            return_pct,
        )

        outcome = CommitteeOutcome(
            recommendation_timestamp=recommendation_timestamp,
            evaluation_timestamp=evaluation_timestamp,
            symbol=symbol.upper().strip(),
            recommendation=normalized_recommendation,
            entry_price=entry_price,
            evaluation_price=evaluation_price,
            return_pct=return_pct,
            successful=successful,
        )

        self._repository.save(
            Event(
                timestamp=evaluation_timestamp,
                event_type=EventType.RECOMMENDATION_OUTCOME_RECORDED,
                symbol=outcome.symbol,
                payload={
                    "recommendation_timestamp": (recommendation_timestamp.isoformat()),
                    "recommendation": outcome.recommendation,
                    "entry_price": outcome.entry_price,
                    "evaluation_price": outcome.evaluation_price,
                    "return_pct": outcome.return_pct,
                    "successful": outcome.successful,
                },
            )
        )

        return outcome
