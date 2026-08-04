from pydantic import BaseModel


class CommitteeMemberStatisticsResponse(BaseModel):
    member: str
    recommendations: int
    buy: int
    hold: int
    sell: int
    average_confidence: int
