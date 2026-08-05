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

    #: The conviction put into words, e.g. "High Conviction". Worded by the
    #: backend so no surface invents its own thresholds.
    conviction_label: str

    committee_agreement: int

    #: How calm this security's own price history is, higher being safer.
    #:
    #: This was the *account's* risk level, printed under a security's name
    #: and labelled "Risk" — so ten cards read "Low" together while the
    #: crypto among them was running 58% volatility and a 75% fall. Null
    #: where the security's own history was too short to measure, which is
    #: never the same as safe.
    safety_score: int | None

    summary: str
    why_now: list[str]
    risks: list[str]
    expected_holding_period: str

    #: What the Artificial CIO decided about this holding before. Null until
    #: a decision has been recorded for it.
    previous_decisions: str | None = None


class BriefingLineResponse(BaseModel):
    """One counted fact about today."""

    statement: str

    #: True where the line is news, false where it is the reassurance
    #: that there is none. Both are printed; only one is styled as news.
    notable: bool


class TodayBriefingResponse(BaseModel):
    """
    The first thing the investor reads, and on most days the only thing.

    Counted facts, worded by the backend. `headline` is null on a day
    where nothing asks for attention — the most common answer, and one
    the page shows as itself rather than filling the space.
    """

    lines: list[BriefingLineResponse]
    headline: str | None
    is_quiet: bool


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
    #: What the investor needs to know today, before anything else. The
    #: page leads with this; the portfolio's own statistics sit below it,
    #: because "what do I own" is not the question a morning starts with.
    today: TodayBriefingResponse

    headline: str
    summary: str
    confidence: float | None = None
    portfolio_health: float

    #: The health score put into words, e.g. "Healthy". Worded by the
    #: backend so no surface invents its own thresholds.
    portfolio_health_label: str

    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[RankedInvestmentCaseResponse]
    changes: list[ChangeResponse] = []
