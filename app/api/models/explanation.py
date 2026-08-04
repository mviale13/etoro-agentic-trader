from pydantic import BaseModel


class ExplanationResponse(BaseModel):
    recommendation: str
    confidence: int
    reasons: list[str]
