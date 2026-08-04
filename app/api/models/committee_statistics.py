from pydantic import BaseModel


class CommitteeStatisticsResponse(BaseModel):
    recommendations: int
    buy: int
    hold: int
    sell: int
    average_confidence: int
