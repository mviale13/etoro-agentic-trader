"""The complete investment case for one security, over the wire.

Composed from the canonical pipeline outputs — ExecutiveDecision,
InvestmentThesis, DecisionEvidence, CommitteeOpinion and Provenance — and
from nothing else. The dashboard renders this response; it does not hold a
dossier model of its own, and no figure here is derived at the API layer.
"""

from datetime import datetime

from pydantic import BaseModel

from app.api.models.portfolio_briefing import ActionResponse, TrendResponse


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


class CommitteeEvidenceResponse(BaseModel):
    """A traceable fact a committee weighed."""

    statement: str
    source: str


class CommitteeOpinionResponse(BaseModel):
    """One committee's view — or its honest inability to form one."""

    committee: str
    recommendation: str

    #: How sure the committee is of its own view. None when it abstained.
    confidence: float | None

    #: True when the committee could not form a view at all. An abstention
    #: is not opposition, and no surface may render it as one.
    abstained: bool

    summary: str
    evidence: list[CommitteeEvidenceResponse]


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

    # ── The narrative (Communication layer, optional) ───────────────
    #: The case in words, or null with the reason beside it. Exactly one
    #: of the two is meaningful: a narrative carries no absent reason,
    #: and an absence always says why.
    narrative: NarrativeResponse | None = None
    narrative_absent: str | None = None
