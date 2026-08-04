from fastapi import APIRouter, HTTPException

from app.api.models.recommendation_explanation import (
    CommitteeVoteResponse,
    RecommendationExplanationResponse,
)
from app.domain.event_type import EventType
from app.repositories.json_event_repository import (
    JsonEventRepository,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.get(
    "/latest",
    response_model=RecommendationExplanationResponse,
)
async def latest_recommendation() -> RecommendationExplanationResponse:
    repository = JsonEventRepository()

    events = [
        event
        for event in repository.load_latest(50)
        if event.event_type == EventType.RECOMMENDATION_GENERATED
    ]

    if not events:
        raise HTTPException(
            status_code=404,
            detail="No recommendations available.",
        )

    event = events[0]

    votes = event.payload.get("votes", [])

    return RecommendationExplanationResponse(
        symbol=event.symbol or "",
        recommendation=str(
            event.payload["recommendation"],
        ),
        confidence=int(
            event.payload["confidence"],
        ),
        committee=[
            CommitteeVoteResponse(
                member=str(v["member"]),
                vote=str(v["vote"]),
                confidence=int(v["confidence"]),
                rationale=str(v["rationale"]),
            )
            for v in votes
            if isinstance(v, dict)
        ],
    )
