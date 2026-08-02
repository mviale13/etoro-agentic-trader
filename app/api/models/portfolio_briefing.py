from pydantic import BaseModel

from app.api.models.executive_brief import ExecutivePriorityResponse


class RankedInvestmentCaseResponse(BaseModel):
    """
    One holding, as judged by the Artificial CIO.

    Every field is evidenced by the decision that produced it. Figures the
    platform cannot yet evidence — price targets, upside and downside
    projections — are deliberately absent rather than estimated.
    """

    rank: int
    symbol: str
    recommendation: str
    conviction: int
    committee_agreement: int
    risk_level: str
    summary: str
    why_now: list[str]
    risks: list[str]
    expected_holding_period: str

    #: What the Artificial CIO decided about this holding before. Null until
    #: a decision has been recorded for it.
    previous_decisions: str | None = None


class PortfolioBriefingResponse(BaseModel):
    headline: str
    summary: str
    confidence: float
    portfolio_health: float
    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[RankedInvestmentCaseResponse]
