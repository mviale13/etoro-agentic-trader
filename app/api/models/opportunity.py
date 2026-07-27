from pydantic import BaseModel


class OpportunityResponse(BaseModel):
    company: str
    action: str
    confidence: int
    summary: str
