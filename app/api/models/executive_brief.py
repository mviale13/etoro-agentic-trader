from pydantic import BaseModel


class ExecutivePriorityResponse(BaseModel):
    title: str
    description: str
    urgency: float


class InvestmentCaseResponse(BaseModel):
    symbol: str
    recommendation: str

    #: How far the committees that spoke agreed. Null where none could.
    confidence: float | None = None

    #: The Artificial CIO's own conviction in this decision, 0-100.
    conviction: int = 0

    summary: str

    #: What the Artificial CIO decided about this symbol before. Null when
    #: nothing was recorded, which is reported as absent rather than filled.
    previous_decisions: str | None = None


class ExecutiveBriefResponse(BaseModel):
    symbol: str
    headline: str
    summary: str
    confidence: float | None = None
    portfolio_health: float
    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[InvestmentCaseResponse]
