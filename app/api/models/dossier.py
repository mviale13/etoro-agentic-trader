"""The complete investment case for one security, over the wire.

Composed from the canonical pipeline outputs — ExecutiveDecision,
InvestmentThesis, DecisionEvidence, CommitteeOpinion and Provenance — and
from nothing else. The dashboard renders this response; it does not hold a
dossier model of its own, and no figure here is derived at the API layer.
"""

from datetime import datetime

from pydantic import BaseModel

from app.api.models.portfolio_briefing import (
    ActionResponse,
    ConvictionChangeResponse,
    TrendResponse,
)
from app.api.models.synthesis import DecisionSynthesisResponse
from app.api.models.understanding import UnderstandingResponse


class ProvenanceResponse(BaseModel):
    """Where a reading came from, and how old it is."""

    source: str
    observed_at: datetime

    #: The age as the investor should read it, e.g. "14 minutes ago".
    #: Coarse on purpose — worded by the domain, not re-derived on screen.
    age: str

    #: True when the source could not be reached and this is the most
    #: recent reading there is. The platform is running on memory, and the
    #: investor is told so rather than left to discover it.
    last_known: bool


class RatingDimensionResponse(BaseModel):
    label: str
    score: float


class TokenRatingResponse(BaseModel):
    """A named third party's published rating, carried as theirs.

    Not evidence and not this platform's judgement. It is rendered
    attributed and linked, and it reaches no score, no playbook and no
    decision — the Yahoo boundary, applied to an opinion instead of a
    label.
    """

    source: str
    name: str
    level: str
    score: float
    dimensions: list[RatingDimensionResponse]

    #: When the rater last reviewed it, which is the date that matters.
    reviewed_at: datetime | None

    #: Where the investor can go and check it themselves.
    page_url: str | None
    report_url: str | None

    #: When this platform read it.
    read: ProvenanceResponse


class CommitteeUncertaintyResponse(BaseModel):
    """One thing a committee could not settle, and whether looking again helps."""

    kind: str
    about: str

    #: Whether another cycle of the same work could close it. False for a
    #: question this platform has no layer for, so a surface never
    #: promises a measurement that is not coming.
    resolvable: bool


class CommitteeOpinionResponse(BaseModel):
    """One committee's position — or its honest inability to take one."""

    committee: str

    #: Where the committee stands, never what to do about it. This field
    #: was `recommendation` and carried BUY/SELL, which is the Artificial
    #: CIO's word: a committee naming an action is a committee deciding.
    #:
    #: None when the committee abstained.
    stance: str | None

    #: True when the committee could not take a position at all. An
    #: abstention is not opposition, and no surface may render it as one.
    abstained: bool
    abstained_because: str | None

    #: How well evidenced the position is, worded with its own counts —
    #: never a bare percentage. It measures the reading, not the
    #: security: a low figure says less was seen, never that the business
    #: is worse.
    confidence: str | None

    #: The named rule that produced the stance.
    decided_by: str

    summary: str

    #: The findings behind the position, resolved from the case's own
    #: ledger. Never the committee's own prose, and never the portfolio
    #: and market context that used to sit here — that is identical under
    #: every symbol and is shown, correctly labelled, elsewhere.
    #:
    #: The order is the order the signals reported, not a ranking.
    supporting: list[str]
    opposing: list[str]

    uncertainty: list[CommitteeUncertaintyResponse]


class PlaybookCoverageResponse(BaseModel):
    """One analysis, and whether this playbook asks for it."""

    analyst: str

    #: What it is called, worded by the backend.
    label: str

    covered: bool

    #: Why it is not asked for, where it is not. Null where it is.
    #: An analysis declined and an analysis that failed mean opposite
    #: things about a case, and a reader cannot tell them apart from a
    #: shorter list alone.
    reason: str | None


class PlaybookResponse(BaseModel):
    """The framework this security is evaluated with, and what it covers.

    A sector says what a company sells. This says how it is read — which
    is what actually determines the analysis, and therefore what a reader
    needs in order to understand why one dossier looks unlike another.
    """

    kind: str
    name: str
    explanation: str
    priorities: list[str]

    #: Every analysis this platform can run, each marked as asked for or
    #: declined-with-reason. Never only the ones that ran.
    coverage: list[PlaybookCoverageResponse]

    #: False when the provider reported no industry at all, so no
    #: playbook was chosen on evidence and the default is not presented
    #: as a decision.
    classified: bool


class ContributionResponse(BaseModel):
    """One factor a score counted, and what it was worth."""

    statement: str

    #: Never negative on this platform: a factor the company fails earns
    #: no point rather than subtracting one. A surface must not render a
    #: zero as a penalty.
    points: int

    #: Why it scored as it did. A zero is not one thing — `neutral` is a
    #: factor that does not apply, `adverse` is one the company failed.
    sense: str

    #: The rule table's own verdict word. Carried as data so a surface
    #: never recovers it by splitting a sentence.
    verdict: str | None = None


class DerivationResponse(BaseModel):
    """How a counted score reached its number, factor by factor.

    Absent for a score that bands a single reading or averages other
    scores. Those have no decomposition, and a one-row table would dress
    a threshold up as a tally.
    """

    contributions: list[ContributionResponse]
    earned: int
    available: int
    band: str
    score: int

    #: Every band and its number, so the reader sees the whole ruler.
    scale: list[tuple[str, int]]

    #: Points the next band up needs, or null at the top band.
    required: int | None

    #: True where every readable factor scored and the band still fell
    #: short — the score was capped by what could be read, not by the
    #: company. Reported rather than left for a surface to infer.
    capped_by_unreadable_factors: bool

    #: The arithmetic as one checkable line, worded by the backend.
    stated: str

    #: How much of what this score asks for could be read, as numerator
    #: and denominator. A different question from how much of what was
    #: read came back favourable, and both belong on the page.
    established_factors: int | None = None
    candidate_factors: int | None = None

    #: The same, worded by the backend. Null where the score does not
    #: know its own candidate set.
    coverage: str | None = None


class ScoreResponse(BaseModel):
    """One score the decision was made on, and why it is that number.

    `value` is None where the platform did not measure it. That never
    means zero and is never filled in from something else — and `basis`
    then says which measurement was missing.

    The basis travels with the value because most of these scores are a
    band this platform chose applied to a reading it took. A number shown
    without its band reads as an observation about the business.
    """

    value: int | None

    #: The one sentence that turns the reading into the number, worded
    #: where the score is computed. Never assembled here.
    basis: str

    #: The findings the reading itself rests on.
    evidence: list[str]

    #: The arithmetic beneath the score, where it counted factors.
    #: Null where the score has no decomposition.
    derivation: DerivationResponse | None = None

    #: What kind of number this is — measured, derived from the investor's
    #: policy, or assessed against this platform's bands. Printed side by
    #: side these look alike, and the assessment borrows the measurement's
    #: authority unless the difference is stated.
    kind: str

    #: The same, worded for a reader.
    kind_stated: str


class EvidenceScoresResponse(BaseModel):
    """
    The scores the decision was actually made on, each explained.

    Every one of them runs the same way: a higher number is better for the
    investment case. Risk is therefore reported as safety — the same
    reading, turned once, so the set can be compared, averaged or ranked
    without one dimension quietly meaning the opposite of the others.
    """

    quality: ScoreResponse
    evidence: ScoreResponse
    valuation: ScoreResponse

    #: How calm the security's own record is. Higher is safer.
    safety: ScoreResponse

    #: How much room the portfolio has for this security under the
    #: investor's own policy.
    portfolio_fit: ScoreResponse


class NarrativeFindingResponse(BaseModel):
    """One canonical fact the narrative's citations resolve to."""

    id: str
    statement: str
    source: str


class NarrativeSectionResponse(BaseModel):
    """One paragraph, and the finding ids it rests on."""

    section: str
    text: str
    finding_ids: list[str]


class NarrativeResponse(BaseModel):
    """
    The case in institutional language — communication only.

    Written by the Executive Writer from the canonical objects and from
    nothing else; every section cites its findings, the recommendation
    is a validated echo of the decision, and the model that wrote it is
    named. The structured dossier above it remains canonical.
    """

    headline: str
    recommendation: str
    sections: list[NarrativeSectionResponse]
    findings: list[NarrativeFindingResponse]
    model: str
    written: str


class DossierResponse(BaseModel):
    """One complete investment case, as the Artificial CIO holds it."""

    symbol: str

    # ── The decision ────────────────────────────────────────────────
    decision_state: str
    conviction: int

    #: The conviction put into words. Worded by the backend so no surface
    #: invents its own thresholds.
    conviction_label: str

    #: How far the committees that spoke agreed. None where none could —
    #: which is not the same as their having disagreed.
    committee_agreement: float | None

    rationale: str

    #: Which way this case has been moving across recorded decisions.
    #: None when nothing was recorded — no history is claimed that does
    #: not exist, and a first review is not a stable one.
    trend: TrendResponse | None

    #: What to consider doing about this security.
    action: ActionResponse | None

    #: How this security is read, and what that framework covers. Null
    #: where nothing about the security itself could be gathered.
    playbook: PlaybookResponse | None

    #: How far conviction moved since the last decision, and why.
    conviction_change: ConvictionChangeResponse | None

    decided_at: datetime

    # ── The thesis ──────────────────────────────────────────────────
    summary: str
    expected_holding_period: str
    catalysts: list[str]
    invalidation_conditions: list[str]
    next_trigger: str | None

    # ── Security evidence ───────────────────────────────────────────
    #: False when nothing about the security itself could be gathered —
    #: a different situation from a security that was analysed and had
    #: gaps, and the two must not share a rationale.
    security_evidenced: bool

    #: Every finding read about this security, favourable or not.
    evidence_weighed: list[str]

    #: The findings that argue for the security — a selection, not the
    #: whole list wearing a flattering label.
    strengths: list[str]

    #: The findings that argue against it.
    risks: list[str]

    missing_evidence: list[str]
    scores: EvidenceScoresResponse

    # ── Portfolio and market context ────────────────────────────────
    #: Facts about the account and the conditions, not the security.
    #: Kept apart so "Healthy liquidity" is never read as a fact about
    #: the security it happens to be printed beside.
    context_strengths: list[str]
    context_risks: list[str]

    # ── The committees ──────────────────────────────────────────────
    committees: list[CommitteeOpinionResponse]

    # ── Provenance ──────────────────────────────────────────────────
    #: When the security's own evidence was read. None where none was.
    evidence_as_of: ProvenanceResponse | None

    #: A third party's published rating of this token, where one has
    #: been read. Shown, attributed, and consumed by nothing.
    token_rating: TokenRatingResponse | None = None

    # ── The narrative (Communication layer, optional) ───────────────
    #: The case in words, or null with the reason beside it. Exactly one
    #: of the two is meaningful: a narrative carries no absent reason,
    #: and an absence always says why.
    narrative: NarrativeResponse | None = None
    narrative_absent: str | None = None

    # ── What this platform understands about the company ────────────
    #: The two understandings derived from the company's own filing:
    #: how the business creates value, and what its statements measure.
    #:
    #: Beside the case, never inside it. Nothing here reached the
    #: decision above — no analyst consumes an understanding, and the
    #: recommendation would be identical if this field were absent. It
    #: is here so an investor can see the filing-grade facts the
    #: platform holds, and the gaps it holds instead.
    #:
    #: Read from the stores only. Composing a dossier never reads a
    #: filing or asks a model, so a company nothing has been observed
    #: for arrives with both halves absent and their reasons worded.
    understanding: UnderstandingResponse | None = None

    # ── The conclusion, stated so it can be challenged ──────────────
    #: The decision as because / despite / review if, composed from the
    #: canonical objects above and deciding nothing. Where `rationale`
    #: says which gate the case reached, this says what it rests on,
    #: what argues against it, and what would occasion a second look —
    #: or reports plainly that the case records no such condition.
    synthesis: DecisionSynthesisResponse | None = None


class NarrativeOutcomeResponse(BaseModel):
    """The written case, or the worded reason there is none. Never both.

    Its own resource because it is its own wait: the dossier's evidence
    is ready in under two seconds and the wording takes fifteen to
    twenty, all of it one model call. A reader gets the decided case
    immediately and the prose when it arrives.
    """

    symbol: str
    narrative: NarrativeResponse | None
    narrative_absent: str | None
