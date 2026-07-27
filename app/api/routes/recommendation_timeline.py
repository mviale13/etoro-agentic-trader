from fastapi import APIRouter, Query

from app.api.models.recommendation_timeline import (
    RecommendationEventResponse,
    RecommendationReplayResponse,
    RecommendationTimelineResponse,
)
from app.domain.event import Event
from app.repositories.json_event_repository import JsonEventRepository
from app.services.recommendation_timeline_service import (
    RecommendationTimelineService,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


def _event_response(event: Event) -> RecommendationEventResponse:
    return RecommendationEventResponse(
        timestamp=event.timestamp,
        symbol=event.symbol,
        payload=event.payload,
    )


@router.get(
    "/timeline",
    response_model=RecommendationTimelineResponse,
)
async def recommendation_timeline(
    limit: int = Query(default=20, ge=1, le=100),
) -> RecommendationTimelineResponse:
    timeline = RecommendationTimelineService(
        JsonEventRepository(),
    ).latest(limit)

    return RecommendationTimelineResponse(
        items=[
            RecommendationReplayResponse(
                recommendation=_event_response(item.recommendation),
                outcome=(
                    _event_response(item.outcome) if item.outcome is not None else None
                ),
            )
            for item in timeline.items
        ]
    )
