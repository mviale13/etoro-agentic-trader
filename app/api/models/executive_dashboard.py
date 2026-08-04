from pydantic import BaseModel

from app.api.models.committee_statistics import (
    CommitteeStatisticsResponse,
)


class ExecutiveDashboardResponse(BaseModel):
    committee: CommitteeStatisticsResponse
    committee_accuracy: int
    investor_understanding: int
