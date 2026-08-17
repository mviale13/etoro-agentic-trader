from pydantic import BaseModel

from app.api.models.portfolio_briefing import TrendResponse


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

    #: Null where the CIO withheld one. Never zero, never substituted.
    conviction: int | None

    #: The conviction put into words, e.g. "High Conviction". Worded by the
    #: backend so no surface invents its own thresholds, and null where
    #: there is no conviction to word.
    conviction_label: str | None

    #: Null where the platform did not measure it. Never zero, never
    #: substituted from something else.
    quality_score: int | None = None
    valuation_score: int | None = None

    #: How calm this security's own price history is — its volatility and
    #: its deepest observed fall, turned so that higher is safer, the way
    #: every other score here runs. Null when that history is too short:
    #: an unmeasured risk is never reported as a safe security.
    safety_score: int | None = None

    evidence_score: int

    #: How much room the portfolio has for this security under the
    #: investor's own policy — funding room and concentration room. Null
    #: where the policy states no limit it could be measured against.
    portfolio_fit_score: int | None = None

    #: How old the security's evidence is, as the investor should read it
    #: — "Yahoo Finance, 14 minutes ago". Null where none was read.
    evidence_as_of: str | None = None

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
    #: Which way this case has been moving across recorded decisions.
    #: Null until one has been recorded.
    trend: TrendResponse | None = None


class WatchedCandidateResponse(BaseModel):
    """
    A watched security the cycle could not judge, by name.

    The funnel counts these; this names them. A security silently absent
    from the candidate list reads as considered-and-dismissed, which is a
    different claim from "nobody looked" or "nothing could be read".
    """

    symbol: str
    name: str

    #: The watchlist that names it.
    source: str


class ResearchPipelineResponse(BaseModel):
    funnel: ResearchFunnelResponse
    candidates: list[ResearchCandidateResponse]

    #: Reviewed — a fundamentals request was spent — but no evidence came
    #: back, so the CIO deliberately did not judge them.
    unevidenced: list[WatchedCandidateResponse]

    #: Not looked at this cycle: each review costs a rate-limited request,
    #: and these fell outside the cycle's budget.
    not_reviewed: list[WatchedCandidateResponse]
