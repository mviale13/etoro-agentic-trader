from pydantic import BaseModel


class ExecutivePriorityResponse(BaseModel):
    title: str
    description: str
    urgency: float

    #: The urgency banded into an attention queue: "now", "today" or
    #: "monitor". Worded by the backend so every surface says the same thing.
    urgency_band: str


class InvestmentCaseResponse(BaseModel):
    symbol: str
    recommendation: str

    #: How far the committees that spoke agreed. Null where none could.
    confidence: float | None = None

    #: The Artificial CIO's own conviction in this decision, 0-100.
    conviction: int = 0

    #: The conviction put into words, e.g. "High Conviction". Worded by the
    #: backend so no surface invents its own thresholds.
    conviction_label: str = "Low Conviction"

    summary: str

    #: What the Artificial CIO decided about this symbol before. Null when
    #: nothing was recorded, which is reported as absent rather than filled.
    #: Which way this case has been moving across recorded decisions.
    #: Null until one has been recorded.
    trend: str | None = None


class ExecutiveBriefResponse(BaseModel):
    symbol: str
    headline: str
    summary: str
    confidence: float | None = None
    portfolio_health: float

    #: The health score put into words, e.g. "Healthy". Worded by the
    #: backend so no surface invents its own thresholds.
    portfolio_health_label: str

    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[InvestmentCaseResponse]
