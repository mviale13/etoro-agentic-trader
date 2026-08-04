from datetime import datetime

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


class ChangeResponse(BaseModel):
    """
    One thing that measurably changed since the previous cycle.

    A decision the Artificial CIO moved, or a market classification that
    moved between two recorded observations. Both are read back out of a
    record; neither is recomputed here, and a quiet feed means nothing
    moved rather than that nothing was looked at.

    An individual instrument's move is not reported, because deciding
    which move matters needs a threshold this platform does not measure.
    """

    title: str
    description: str
    category: str
    severity: str
    timestamp: datetime
    action_required: bool


class PortfolioBriefingResponse(BaseModel):
    headline: str
    summary: str
    confidence: float | None = None
    portfolio_health: float
    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[RankedInvestmentCaseResponse]
    changes: list[ChangeResponse] = []
