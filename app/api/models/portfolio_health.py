from pydantic import BaseModel


class PortfolioHealthResponse(BaseModel):
    score: int
    summary: str
