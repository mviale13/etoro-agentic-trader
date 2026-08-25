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


class DossierDefinitionResponse(BaseModel):
    """What kind of investment case this dossier is, declared by the backend.

    The asset-specific definition beneath the shared shell: what the case
    is titled, how the classification card is headed, and whether
    filing-grade sections apply to this subject at all. The page renders
    these strings and decides nothing — an equity and a crypto dossier
    differ because the domain says so, never because a surface inferred
    an asset class.
    """

    kind: str

    #: What the case is called at the top of the page.
    title: str

    #: The heading over the classification section — industry beside the
    #: earned playbook, two concepts held apart. A token has an asset
    #: type instead.
    classification_heading: str

    #: The heading over the analysis-framework card: which analysts are
    #: asked and what the case is read for. Worded as what it is, so the
    #: frame the industry route chose is never presented as a
    #: classification this platform earned.
    analysis_heading: str

    #: Whether filing-grade understanding belongs on this dossier. False
    #: where the subject publishes no filings — then the reason says so
    #: as a property of the asset class, never as missing evidence, and
    #: the understanding sections are not sent at all.
    filings_apply: bool
    filings_inapplicable_because: str | None


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


class FundamentalRowResponse(BaseModel):
    """One fundamentals metric under its honest authority.

    `standing` is the row's whole meaning: filing evidence, an
    explicitly labelled provider fallback (possibly last-known), an
    absence in the filing route's own words, or a refusal with its
    reason. The page renders `because` verbatim and derives nothing.
    """

    metric: str
    label: str

    #: The figure, read through `unit`. None exactly where the standing
    #: shows none — a measured zero is a figure, never an absence.
    value: float | None
    unit: str
    standing: str

    source: str | None
    as_of: str | None

    #: ISO code where the provider's own record establishes one. Never
    #: inferred, and only meaningful for currency-unit rows.
    currency: str | None

    #: The reporting period where established. The stored provider
    #: record establishes none, so fallback rows always carry None.
    period: str | None

    because: str

    #: The filing arithmetic, for filing-evidence rows only.
    stated: str | None


class FundamentalsResponse(BaseModel):
    """The compact fundamentals section: one explanation, twelve rows."""

    explained: str
    rows: list[FundamentalRowResponse]


class FundCostResponse(BaseModel):
    """What owning a fund costs, as the provider reports it.

    An evidenced fact about the wrapper, and only that: it reaches no
    score, no band and no verdict, and it is served with the moment it
    was read. `stated` is the backend's own sentence — the frontend
    renders it and never rewords a ratio into a judgement.
    """

    stated: str

    #: Decimal ratio of assets per year: 0.0007 is 0.07%.
    expense_ratio: float

    #: When this platform read it, and from where.
    read: ProvenanceResponse


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


class TokenFactRowResponse(BaseModel):
    """One market fact about a token, with its standing beside it.

    `stated` is the value already worded — "$18.3bn", "336,685,219",
    "33.7%" — or null where the standing serves none, and `because`
    then says why. The standing is what stops a provider claim reading
    with an established fact's authority, and a MOVRvest calculation
    masquerading as a provider observation.
    """

    label: str

    stated: str | None

    #: "established" | "claimed" | "rejected" | "absent" | "calculated"
    standing: str

    #: The same, worded for a reader by the backend.
    standing_stated: str

    #: Who reported it. Null for MOVRvest-calculated rows and absences.
    source: str | None

    #: How old the observation is, worded by the domain. Null where
    #: nothing was observed.
    age: str | None

    #: The account of the standing: what corroborated it, what nothing
    #: could check, or why it is absent.
    because: str | None

    #: Every source whose independent agreement established this value —
    #: the served claimant first, then the corroborators, exactly as the
    #: gate ordered them. Empty for every standing but ESTABLISHED,
    #: because nothing agreed, and empty for MOVRvest-calculated rows,
    #: which have no provider claimants at all.
    #:
    #: Carried structurally rather than left in prose: a surface that
    #: must name the claimants may not parse a sentence to find them,
    #: and a sentence is not a list. Nothing here is inferred from
    #: `source` — one served claimant is not the set that agreed.
    claimants: list[str] = []

    #: The versioned rule under which this standing was reached, so a
    #: figure on the page names what admitted it instead of arriving as
    #: a bare number. Null where no rule admitted it — a claim, a
    #: conflict, an absence and a MOVRvest calculation all carry null,
    #: and none of them may have one manufactured from the standing.
    rule: str | None = None


class TokenFactGroupResponse(BaseModel):
    """One group of the asset profile — Market, Supply, Dilution…"""

    title: str
    rows: list[TokenFactRowResponse]


class RejectedReadingResponse(BaseModel):
    """A claim that failed validation, retained rather than discarded."""

    statement: str


class AssetProfileResponse(BaseModel):
    """What is measured about this asset, judged before it is served.

    The crypto counterpart of the filing sections a company dossier
    carries. Every provider observation is dated and attributed; every
    derived figure identifies itself as this platform's arithmetic over
    established inputs; and the claims that failed validation are
    disclosed with their reasons rather than silently replaced.
    """

    groups: list[TokenFactGroupResponse]

    #: The validation gate's rejection ledger, worded by the domain.
    rejected: list[RejectedReadingResponse]


class ProtocolFactResponse(BaseModel):
    """One figure about the economic system behind a token."""

    metric: str
    label: str

    #: What this metric is evidence about: capital, activity, value
    #: generation, or what reaches holders. Never collapsed together.
    family: str

    stated: str | None

    #: The window the figure covers, or null for a level.
    window: str | None

    standing: str
    standing_stated: str

    #: available | not_applicable | unavailable_free |
    #: semantics_unresolved | identity_unresolved — five different
    #: situations, never one "missing".
    availability: str
    availability_stated: str

    source: str | None
    age: str | None

    #: The provider's own definition of this metric for this entity,
    #: verbatim. The sentence that says a protocol keeps no fees and
    #: sends 99% to a fund that buys the token is the mechanism, and
    #: paraphrasing it would be this platform inventing one.
    provider_methodology: str | None

    because: str | None


class ProtocolEntityResponse(BaseModel):
    """One economic system, and the figures measured over it."""

    key: str
    name: str

    #: "chain" or "protocol" — what kind of thing this is.
    kind: str

    #: What generated these figures, in one sentence.
    measures: str

    #: Why this entity is attached to this security. A shared name is
    #: never a basis: the same name covers a venue with $842k of daily
    #: fees and a chain with $3.8k.
    mapping_basis: str

    #: False where the entity is real and what its economics mean for
    #: the token is not settled.
    mapping_settled: bool

    facts: list[ProtocolFactResponse]


class DerivedFigureResponse(BaseModel):
    """Arithmetic this platform performed over a protocol observation."""

    label: str
    stated_value: str

    #: The arithmetic in one line, naming the observation beneath it.
    stated: str

    #: What this figure is not, said plainly. A run rate is not a year
    #: that happened.
    caveat: str


class ProtocolFundamentalsResponse(BaseModel):
    """The economics behind a token — evidence, never conclusions.

    A separate evidence family from the token's own market facts, and
    independent of them: a market value can be CONFLICTED while the
    protocol's fees are perfectly well attributed. Consumed by no
    score, no playbook and no decision.
    """

    entities: list[ProtocolEntityResponse]

    #: This platform's own arithmetic, held apart from the observations.
    derived: list[DerivedFigureResponse]

    #: Why nothing is measured, where no economic system is mapped.
    unmapped_because: str | None


class AnalyticalCapabilityResponse(BaseModel):
    """One analytical lens this asset is read through."""

    key: str
    label: str

    #: What the lens looks at, in one sentence.
    reads: str


class ConsideredArchetypeResponse(BaseModel):
    """An archetype weighed and not chosen, with the reason."""

    archetype: str
    not_chosen_because: str


class QuestionEvidenceResponse(BaseModel):
    """One evidence demand of one question, met or unmet."""

    #: What would answer it, in words. Present whether or not anything
    #: does — an unmet demand is the acquisition roadmap, and dropping
    #: it would turn the roadmap into a list of things that worked.
    demand: str

    met: bool

    #: The figure, or the source's own definition where the demand
    #: asked for the definition rather than the figure.
    stated: str | None

    standing: str
    standing_stated: str

    source: str | None
    age: str | None

    #: Which economic entity supplied it. Never omitted for a security
    #: with more than one.
    entity: str | None

    because: str | None


class CryptoQuestionResponse(BaseModel):
    """One investment question against one token."""

    key: str
    label: str
    asks: str
    matters_because: str

    #: ask | ask_evidence_insufficient | not_applicable | undetermined.
    #: The product of two independent facts: whether the question
    #: applies to this kind of asset, and whether anything established
    #: answers it. Neither was allowed to decide the other.
    cell: str
    cell_stated: str

    #: The applicability alone, decided from the archetype and from no
    #: figure whatsoever.
    applicability: str
    applicability_because: str

    #: The lens that asks it, where it is asked.
    asked_by: str | None

    #: The firmest standing anything answering this reaches.
    best_standing: str
    best_standing_stated: str

    evidence: list[QuestionEvidenceResponse]


class ValueChainLinkResponse(BaseModel):
    """One stage of one entity's value chain."""

    stage: str
    label: str

    stated: str | None
    window: str | None

    standing: str
    standing_stated: str
    availability_stated: str

    #: The source's own definition of this figure, verbatim.
    methodology: str | None

    because: str | None


class ValueChainResponse(BaseModel):
    """How one economic entity's value moves, from use to the token.

    One per entity and never one per security: Hyperliquid's venue and
    its chain are 224x apart on fees, and a chain that summed them
    would misstate the business by that factor.
    """

    entity: str
    kind: str
    measures: str
    mapping_settled: bool

    links: list[ValueChainLinkResponse]

    #: What the source's wording says happens at the last stage —
    #: burned, buys the token, paid to holders, or no mechanism at all.
    #: The word "fees" means a different thing at each.
    mechanism: str
    mechanism_stated: str

    #: The source's own sentence, verbatim, where it published one.
    mechanism_source_wording: str | None

    because: str


class CryptoPlaybookResponse(BaseModel):
    """Which investment questions this token is asked, and which it is not.

    Applicability, evidence demands and evidence standing — never a
    verdict. Nothing here is scored, banded or ranked, and no factor
    consumes any of it.
    """

    archetype: str
    name: str
    explanation: str

    confidence: str
    confidence_stated: str

    because: str

    #: The evidence the archetype rests on, each line checkable.
    rests_on: list[str]

    #: What the archetype does not establish. A kind is not a verdict.
    does_not_establish: list[str]

    alternatives: list[ConsideredArchetypeResponse]

    #: Evidence held here and deliberately not used to classify.
    not_classified_from: list[str]

    capabilities: list[AnalyticalCapabilityResponse]

    #: Questions this archetype is known to need and this platform has
    #: not modelled — the boundary that keeps a future stablecoin out
    #: of a monetary asset's questions.
    unmodelled: list[str]

    questions: list[CryptoQuestionResponse]

    chains: list[ValueChainResponse]

    unmapped_because: str | None


class MarketObservationResponse(BaseModel):
    """One market figure, with its interval and its universe."""

    metric: str
    label: str

    #: What it covers in time. Never dropped, and never generalised into
    #: a "trend" — that word is an interpretation nothing here makes.
    interval: str
    interval_stated: str

    stated: str | None

    standing: str
    standing_stated: str

    #: True where this platform computed it rather than read it.
    derived: bool

    #: The set of assets it was computed over, where it is an aggregate.
    universe: str | None

    source: str | None
    age: str | None

    because: str | None


class RelativeReturnResponse(BaseModel):
    """One asset's return against one comparator's, over the same interval."""

    interval: str
    comparator: str

    subject_return: str
    comparator_return: str

    #: The difference in percentage points, already worded.
    delta: str

    standing: str

    #: The arithmetic in one line, worded by the domain.
    stated: str

    caveat: str | None


class ConcentrationResponse(BaseModel):
    """How much of a comparator this asset itself is."""

    comparator: str
    stated: str


class PeerGroupResponse(BaseModel):
    """The externally observed group this asset is compared against.

    A vendor's category, carried under the vendor's name. It is **not**
    this platform's analytical archetype and never modifies one: an
    asset read as a smart-contract network can sit in a market group
    that contains Bitcoin, and both statements are true.
    """

    key: str
    name: str
    provider: str
    selected_because: str
    caveats: list[str]


class ConsideredPeerGroupResponse(BaseModel):
    """A group weighed and rejected, with what the measurement showed."""

    name: str
    rejected_because: str


class CryptoMarketContextResponse(BaseModel):
    """What the market did, what the peers did, and what this asset did.

    Market context, never Asset Quality. Nothing here is banded, scored
    or ranked, and a token that fell less than its peers is not thereby
    a better asset.
    """

    #: The environment, shared by every token in the book.
    market: list[MarketObservationResponse]

    market_source: str | None
    market_age: str | None

    #: This asset's own returns, one per interval published.
    returns: list[MarketObservationResponse]

    peer: PeerGroupResponse | None

    #: Why there is no peer group. Set exactly when `peer` is null — a
    #: missing comparison is stated rather than left blank.
    peer_unavailable_because: str | None

    considered: list[ConsideredPeerGroupResponse]

    peer_observations: list[MarketObservationResponse]

    relative: list[RelativeReturnResponse]

    concentrations: list[ConcentrationResponse]

    #: Intervals this asset's return was read at and no comparator was.
    uncompared: list[str]

    unavailable_because: str | None


class SupplyFigureResponse(BaseModel):
    """One supply quantity, under one concept and one methodology."""

    concept: str
    concept_stated: str

    stated: str

    #: Whose definition decided what is in the number.
    defined_by: str
    methodology: str

    #: Whether this platform knows what the definition leaves out.
    disclosed: bool

    excludes: list[str]

    source: str
    age: str | None

    #: The label the source published it under, where it differs.
    reported_as: str | None

    standing: str
    standing_stated: str

    #: primary_observation | primary_derived | secondary_aggregate …
    authority: str
    authority_stated: str

    because: str | None
    caveats: list[str]


class SupplyComparisonResponse(BaseModel):
    """What two supply figures are to each other.

    `coexist` is the state this whole layer exists to make possible: two
    numbers that differ because they count different things, which is
    information rather than a contradiction.
    """

    verdict: str
    verdict_stated: str

    left_source: str
    left_stated: str
    right_source: str
    right_stated: str

    #: Which supply concept each side claims, carried from the domain's
    #: own `SupplyFact.concept` so a surface can group a comparison
    #: under the quantity it is about.
    #:
    #: **Two fields, not one, because a comparison may span two
    #: concepts.** `compare()` returns `coexist` exactly when the two
    #: sides claim *different* quantities — "different quantities, both
    #: able to be right" — and ADA carries one live. A single `concept`
    #: would have to name a winner, which is the thing this vocabulary
    #: exists to refuse.
    left_concept: str
    right_concept: str

    because: str


class SupplyPictureResponse(BaseModel):
    """A token's supply, read as a vocabulary rather than as one number.

    Facts and relationships only. No dilution, no band, no verdict —
    what a supply structure implies for an investment case is a question
    for a layer that does not exist.
    """

    #: Grouped by concept, in reading order.
    figures: list[SupplyFigureResponse]

    comparisons: list[SupplyComparisonResponse]

    #: True where two claims to the same quantity differ and at least
    #: one party does not publish what it excludes.
    methodology_disagreement: bool

    #: What is still missing, named rather than left blank.
    unresolved: list[str]

    unavailable_because: str | None


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


class RecordedTransitionResponse(BaseModel):
    """One time the Artificial CIO changed its mind, and what moved under it.

    Composed from two adjacent journal records. The rationale is the one
    recorded *at the time*, never a sentence written now about a decision
    taken then.
    """

    at: datetime

    from_state: str
    to_state: str
    #: Either side may be absent, and an absent conviction is never a
    #: low one — `stated` above leaves the clause out entirely.
    from_conviction: int | None
    to_conviction: int | None

    #: The change in one line, worded by the domain.
    stated: str

    #: The rationale the CIO recorded with the later decision, verbatim.
    rationale: str

    #: Each score that measurably differed, worded. A score that stopped
    #: being measurable says so — it is not a score that fell.
    moved: list[str]

    #: True where a record predates the journal keeping scores, so what
    #: moved underneath cannot be said. Then `moved` is empty, and that
    #: emptiness means "cannot be said" rather than "nothing moved".
    unexplained: bool


class DecisionCourseResponse(BaseModel):
    """Every recorded change of mind about this security.

    The journal has held this all along — it is what the home page's
    change feed is built from — while the dossier said only "Stable".
    It reports what was recorded and judges none of it: whether those
    decisions were right is the track record's question.
    """

    reviews: int
    changes: int

    first_recorded_at: datetime | None
    last_recorded_at: datetime | None

    #: Most recent first.
    transitions: list[RecordedTransitionResponse]

    #: The course in one sentence, worded by the domain.
    stated: str

    #: Why there is no course to show — a first review has nothing before
    #: it to have changed from. Null where there is one.
    absent_because: str | None


class IndustryContextResponse(BaseModel):
    """Where the market files this company — context, never a conclusion.

    The provider's own industry and sector strings, served with the
    moment they were read. Contextual knowledge about where the company
    operates: it does not become filing-grounded by appearing beside
    grounded understanding, and it never substitutes for the earned
    playbook beside it.
    """

    #: The one line a surface prints large. The industry string where the
    #: provider reports one; the backend's own absence wording otherwise.
    label: str

    industry: str | None
    sector: str | None

    #: The backend's sentence for this state — presence or either kind of
    #: absence (the provider reports none, or no profile was ever
    #: acquired). Rendered verbatim.
    stated: str

    #: When this platform read it, and from where. Null where no provider
    #: profile has been acquired at all.
    read: ProvenanceResponse | None


class EarnedPlaybookResponse(BaseModel):
    """The investment playbook this platform established, or the honest state.

    The grounded selection over Business Understanding — the canonical
    two-route selector's authoritative half, read from stored knowledge
    only. Exactly one of three states, never collapsed:

    - ``established`` — a quorate understanding fired an earned rule.
    - ``refused`` — the grounded route itself declined, with its reason.
    - ``unavailable`` — no current reading of the company's filing is
      held, so there is nothing to select from.

    A refusal and an absence are different facts about the platform's
    knowledge, and neither is ever dressed as a classification.
    """

    state: str

    #: The playbook's investor-facing name — "Bank", "Industrial" — only
    #: where the state is ``established``. Never a default.
    playbook: str | None

    #: The one line a surface prints large: the playbook name where
    #: established, the backend's own state wording otherwise.
    label: str

    #: The owning layer's sentence, verbatim: the rule's reasoning where
    #: established, the grounded route's refusal where refused, the
    #: store's absence where unavailable.
    stated: str

    #: What the conclusion rests on, worded with its count — e.g. a claim
    #: settled at 3 of 5. Present only where established, and only where
    #: the understanding named one.
    narrowest_agreement: str | None


class ClassificationResponse(BaseModel):
    """Industry and the earned playbook, beside each other and never blended.

    Two classifications answering two questions: where the company
    operates (the provider's category — context) and what kind of
    economic business this platform established it to be (the earned
    playbook — analysis). An apparent mismatch between them is
    information, not a defect, and the section says so once.
    """

    industry: IndustryContextResponse
    playbook: EarnedPlaybookResponse

    #: The backend's own sentence separating the two concepts, rendered
    #: once for the section.
    distinction: str


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

    #: What this score is called on this dossier, worded by the domain's
    #: dossier definition. The same reading is "Business quality" on an
    #: equity and "Asset quality" on a token: the number and its bands
    #: are identical, and the label is what stops a network reading
    #: presenting itself as a judgment about a business.
    label: str

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

    # ── What kind of case this is ───────────────────────────────────
    #: The asset-specific definition beneath the shared shell: title,
    #: classification heading, and which sections belong. Declared here
    #: so no surface infers an asset class from the shape of the data.
    definition: DossierDefinitionResponse

    # ── The decision ────────────────────────────────────────────────
    decision_state: str

    #: Null where the CIO withheld one, which it does wherever the case
    #: cites no supporting reason. Never zero, and never substituted:
    #: the state is the decision, and the number is a separate claim.
    conviction: int | None

    #: The conviction put into words. Worded by the backend so no surface
    #: invents its own thresholds — and null where there is no conviction
    #: to word, because "Low Conviction" is a judgment nobody made.
    conviction_label: str | None

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

    #: Industry beside the earned playbook — the two classifications an
    #: investor needs held apart, each in its honest state. Null where
    #: the subject is not a company (its own sections carry its
    #: semantics), and composed from stored evidence only.
    classification: ClassificationResponse | None

    #: How far conviction moved since the last decision, and why.
    conviction_change: ConvictionChangeResponse | None

    #: Every recorded change of mind about this security, with the
    #: rationale recorded at the time and what moved beneath it. Read
    #: from the decision journal only; it reaches no score and no
    #: decision.
    decision_course: DecisionCourseResponse | None

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

    #: What owning the fund costs, where the provider reported it. A
    #: fact with a date, consumed by nothing. Null for anything that is
    #: not a fund.
    fund_cost: FundCostResponse | None = None

    #: The token's market facts, judged through the validation gate —
    #: standings, dates, sources and the rejection ledger. Null for
    #: anything that is not a cryptocurrency.
    asset_profile: AssetProfileResponse | None = None

    #: The economics of the system behind the token, attributed and
    #: dated. Its own evidence family, independent of the market facts
    #: above and consumed by nothing. Null for anything that is not a
    #: cryptocurrency.
    protocol_fundamentals: ProtocolFundamentalsResponse | None = None

    #: Which investment questions this kind of digital asset is asked,
    #: which are declined and why, and what evidence would answer each.
    #: Applicability and evidence standing, never a verdict. Null for
    #: anything that is not a cryptocurrency.
    crypto_playbook: CryptoPlaybookResponse | None = None

    #: What kind of crypto market this asset is trading inside, and its
    #: place in it. Its own evidence family, separate from the token's
    #: facts and from its protocol's, and consumed by nothing. Null for
    #: anything that is not a cryptocurrency.
    crypto_market: CryptoMarketContextResponse | None = None

    #: What each of this token's supply numbers actually counts, and
    #: which of them really disagree. Facts and relationships; no
    #: dilution reading. Null for anything that is not a cryptocurrency.
    supply: SupplyPictureResponse | None = None

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

    #: The fundamentals the investor asked the dossier for, each under
    #: its honest authority — filing evidence first, an explicitly
    #: labelled provider fallback second, the exact absence third
    #: (owner ruling, 2026-08-23). Presentation only: nothing here
    #: reached the decision, raised any authority, or touched an
    #: envelope, and composing it reads the stores alone. None where
    #: filings do not apply to the subject.
    fundamentals: FundamentalsResponse | None = None

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
