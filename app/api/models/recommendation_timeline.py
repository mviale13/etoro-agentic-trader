from datetime import datetime
from typing import Any

from pydantic import BaseModel


class RecommendationEventResponse(BaseModel):
    timestamp: datetime
    symbol: str | None
    payload: dict[str, Any]


class RecommendationReplayResponse(BaseModel):
    recommendation: RecommendationEventResponse
    outcome: RecommendationEventResponse | None


class RecommendationTimelineResponse(BaseModel):
    items: list[RecommendationReplayResponse]
