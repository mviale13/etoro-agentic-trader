from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    name: str
    score: int
    status: str
    message: str


class HealthResponse(BaseModel):
    score: int
    checks: list[HealthCheckResponse]


class OpinionResponse(BaseModel):
    member: str
    vote: str
    confidence: int
    rationale: str

    #: Why this member took no position, or null where it took
    #: one. Carried explicitly so a client never has to read it
    #: out of the confidence or the rationale text.
    abstained_because: str | None = None


class RecommendationResponse(BaseModel):
    symbol: str
    action: str
    confidence: int
    opinions: list[OpinionResponse]


class TodayResponse(BaseModel):
    greeting: str
    health: HealthResponse
    summary: str
    changes: list[str]
    recommendation: RecommendationResponse
    next_action: str
