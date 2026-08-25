from datetime import datetime

from pydantic import BaseModel

from app.api.models.executive_brief import ExecutivePriorityResponse


class ConvictionChangeResponse(BaseModel):
    """How far conviction moved since the last decision, and why.

    `because` is empty when no score measurably moved, and also when the
    earlier decision predates the scores being recorded — `unexplained`
    tells those two apart, so an honest silence is never rendered as
    "nothing changed".
    """

    previous: int

    #: Signed, and never zero: an unchanged conviction is no change.
    delta: int

    #: The movement as the investor reads it, e.g. "+8 conviction".
    stated: str

    because: list[str]
    unexplained: bool


class TrendResponse(BaseModel):
    """Which way this investment case has been moving."""

    #: "stable" | "improving" | "deteriorating" — for styling, so no
    #: surface has to read the sentence to know which way it points.
    direction: str

    #: The trend as the investor reads it, worded by the backend.
    stated: str


class ActionResponse(BaseModel):
    """What the Artificial CIO asks the investor to consider.

    Deliberately not the recommendation. A RECOMMEND on a security
    already held and one on a security the investor does not own are the
    same judgement and different considerations, and only the portfolio
    knows which case this is.

    A consideration, never an instruction: MOVRvest recommends and the
    investor decides. No size, price or quantity is ever suggested.
    """

    kind: str
    statement: str

    #: The Artificial CIO's own reason, carried rather than rewritten.
    because: str

    #: The next dated thing bearing on this case, or null when nothing is
    #: scheduled — which is not the same as nothing being expected.
    checkpoint: str | None

    #: Whether this consideration puts a decision in front of the
    #: investor — the domain's own reading of the action kind, carried so
    #: a surface comparing this action with a recorded one compares the
    #: same five facts the cycle record states, rather than re-deriving
    #: one of them from the kind string.
    asks_for_something: bool = False


class RankedInvestmentCaseResponse(BaseModel):
    """
    One holding, as judged by the Artificial CIO.

    Every field is evidenced by the decision that produced it. Figures the
    platform cannot yet evidence — price targets, upside and downside
    projections — are deliberately absent rather than estimated.
    """

    #: Position in the conviction order. Null where the case carries no
    #: conviction: there is no order to hold a place in, and a number
    #: here would rank cases against each other on nothing.
    rank: int | None
    symbol: str
    recommendation: str

    #: Null where the CIO withheld one. Never zero, never substituted.
    conviction: int | None

    #: The conviction put into words, e.g. "High Conviction". Worded by the
    #: backend so no surface invents its own thresholds, and null where
    #: there is no conviction to word.
    conviction_label: str | None

    #: Null where no committee spoke. Zero would say they disagreed
    #: completely, which is the opposite of an unasked question.
    committee_agreement: int | None

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

    #: Which way this case has been moving across recorded decisions.
    #: Null until one has been recorded — a first review is not a stable
    #: one, and calling it stable would claim a history that does not
    #: exist.
    trend: TrendResponse | None = None

    #: What to consider doing about this holding.
    action: ActionResponse | None = None

    #: What kind of investment the Artificial CIO reads this as. Null
    #: where nothing about the security itself could be gathered.
    playbook_name: str | None = None

    #: How far conviction moved since the last decision, and what moved
    #: underneath it. Null when it did not move.
    conviction_change: ConvictionChangeResponse | None = None


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
    portfolio_health: float | None

    #: The health score put into words, e.g. "Healthy". Worded by the
    #: backend so no surface invents its own thresholds.
    portfolio_health_label: str

    priorities: list[ExecutivePriorityResponse]
    investment_cases: list[RankedInvestmentCaseResponse]
    changes: list[ChangeResponse] = []
