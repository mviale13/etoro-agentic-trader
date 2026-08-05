"""The Artificial CIO's own decisions, measured against what followed."""

from collections import Counter

from fastapi import APIRouter

from app.api.models.track_record import (
    OutcomeResponse,
    TrackRecordResponse,
    UnscoredReasonResponse,
)
from app.application.learning.decision_journal import DecisionJournal
from app.application.learning.decision_outcome_service import (
    DecisionOutcomeService,
)
from app.domain.decision_outcome import DecisionOutcome, TrackRecord
from app.providers.yahoo_price_history import YahooPriceHistory
from app.repositories.json_event_repository import JsonEventRepository

router = APIRouter(
    prefix="/track-record",
    tags=["track-record"],
)


def _verdict(outcome: DecisionOutcome) -> str:
    """
    The finding in words, worded once here.

    "Not a call" covers both the decisions that implied nothing and the
    securities that barely moved — in either case the outcome is evidence
    for nobody, and the page must not colour it as a result.
    """

    agreed = outcome.moved_as_the_decision_implied

    if agreed is None:
        return "not a call"

    return "as decided" if agreed else "against the decision"


def _payload(record: TrackRecord) -> TrackRecordResponse:
    calls = record.calls

    return TrackRecordResponse(
        recorded=len(record.outcomes) + len(record.unscored),
        measured=len(record.outcomes),
        calls=len(calls),
        agreed=record.agreed,
        # Null below MINIMUM_CALLS: a rate over three decisions is not a
        # rate, and serving one would read as a skill measurement.
        hit_rate=record.hit_rate,
        minimum_calls=TrackRecord.MINIMUM_CALLS,
        unscored_total=len(record.unscored),
        outcomes=[
            OutcomeResponse(
                symbol=outcome.symbol,
                state=outcome.state.value,
                conviction=outcome.conviction,
                decided_on=outcome.decided_at.date().isoformat(),
                priced_on=outcome.priced_on.isoformat(),
                change_pct=round(outcome.change * 100, 2),
                days_elapsed=outcome.days_elapsed,
                agreed=outcome.moved_as_the_decision_implied,
                verdict=_verdict(outcome),
                reading=outcome.reading.stated(),
            )
            for outcome in sorted(
                record.outcomes,
                key=lambda item: item.change,
                reverse=True,
            )
        ],
        # The reasons, not one row per decision: a young journal repeats
        # the same sentence sixty times, and the count is the information.
        unscored_reasons=[
            UnscoredReasonResponse(reason=reason, count=count)
            for reason, count in Counter(
                item.reason for item in record.unscored
            ).most_common()
        ],
    )


@router.get("/", response_model=TrackRecordResponse)
async def track_record() -> TrackRecordResponse:
    record = await DecisionOutcomeService(
        journal=DecisionJournal(JsonEventRepository()),
        prices=YahooPriceHistory(),
    ).build()

    return _payload(record)
