from pydantic import BaseModel


class ExecutivePriorityResponse(BaseModel):
    title: str
    description: str
    urgency: float


class InvestmentCaseResponse(BaseModel):
    symbol: str
    recommendation: str
    confidence: float
    summary: str


class ExecutiveBriefResponse(BaseModel):
    symbol: str
    headline: str
    summary: str
    confidence: float
    portfolio_health: float
    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[InvestmentCaseResponse]
