from pydantic import BaseModel


class CommitteeVoteResponse(BaseModel):
    member: str
    vote: str
    confidence: int
    rationale: str


class RecommendationExplanationResponse(BaseModel):
    symbol: str
    recommendation: str
    confidence: int
    committee: list[CommitteeVoteResponse]
