from pydantic import BaseModel


class ResearchFunnelResponse(BaseModel):
    """How the watchlist narrowed to the candidates the CIO judged."""

    #: Watched securities the portfolio does not hold.
    candidates: int

    #: How many of them this cycle looked at.
    reviewed: int

    #: How many of those could be described on their own evidence.
    evidenced: int

    #: Reviewed but not describable, so deliberately not judged.
    unevidenced: int

    #: Candidates this cycle did not have the budget to look at.
    not_reviewed: int

    judged: int
    actionable: int


class ResearchCandidateResponse(BaseModel):
    """
    One watched security, as judged by the Artificial CIO.

    Every score here is the score the decision was actually made on. Price
    targets and expected upside are absent because the platform cannot
    evidence them, not because they were omitted for brevity.
    """

    rank: int
    symbol: str
    name: str

    #: The watchlist that names it.
    source: str

    recommendation: str
    conviction: int

    quality_score: int
    valuation_score: int
    risk_score: int
    evidence_score: int
    portfolio_fit_score: int

    #: The evidence lines the decision was weighed on, positive or not.
    #: They are reported as the CIO saw them, not filtered into a case.
    evidence_weighed: list[str]

    #: The gate the investment case has not cleared.
    why_not_yet: str

    #: What the case is still missing.
    missing_evidence: list[str]

    catalysts: list[str]
    next_trigger: str | None = None

    #: What the CIO decided about this security before, or null if never.
    previous_decisions: str | None = None


class ResearchPipelineResponse(BaseModel):
    funnel: ResearchFunnelResponse
    candidates: list[ResearchCandidateResponse]
