import type {
  ConvictionChangeViewModel,
  DecisionTrendViewModel,
  ExecutiveActionViewModel,
} from "@/lib/view-models/investment-case";

/**
 * Client for GET /executive/{symbol}/dossier.
 *
 * A strict mirror of the backend's DossierResponse and nothing more: the
 * dashboard holds no dossier model of its own, derives no score, and bands
 * no figure. If the backend renames a field the parse fails loudly instead
 * of silently substituting anything.
 */

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export interface DossierProvenance {
  source: string;
  /** The age as the investor should read it, worded by the backend. */
  age: string;
  /** True when the source was unreachable and this is the last reading. */
  lastKnown: boolean;
}

/** One thing a committee could not settle, and whether looking again helps. */
export interface DossierCommitteeUncertainty {
  kind: string;
  about: string;
  /** False for a question no layer of the platform answers. Never shown
      as pending: that would promise a measurement that is not coming. */
  resolvable: boolean;
}

export interface DossierCommitteeOpinion {
  committee: string;
  /** Where the committee stands — never what to do about it. Null when
      it abstained. Only the Artificial CIO names an action. */
  stance: string | null;
  /** An abstention is not opposition, and is never rendered as one. */
  abstained: boolean;
  abstainedBecause: string | null;
  /** Worded by the backend with its own counts. Never a bare percentage:
      it measures the reading, not the security. */
  confidence: string | null;
  /** The named rule that produced the stance. */
  decidedBy: string;
  summary: string;
  /** The findings the position stands on, resolved from the case's own
      ledger. The order is the order read, and is not a ranking. */
  supporting: readonly string[];
  opposing: readonly string[];
  uncertainty: readonly DossierCommitteeUncertainty[];
}

/**
 * One score, and the backend's own account of why it is that number.
 *
 * `value` null means the platform did not measure it — never zero, and
 * `basis` then says which measurement was missing. The basis is written
 * where the score is computed; nothing on this side composes it.
 */
/** One factor a score counted, and what it was worth. */
export interface DossierContribution {
  statement: string;
  /** Never negative: a failed factor earns no point rather than losing
      one. A zero must never be rendered as a penalty. */
  points: number;
  /** "favourable" | "neutral" | "adverse" — what a zero actually means. */
  sense: string;
  /** The rule table's own word. Carried as data, never recovered by
      splitting a sentence on this side. */
  verdict: string | null;
}

/** How a counted score reached its number. Absent where there is no
    decomposition — a banded reading or an average of other scores. */
export interface DossierDerivation {
  contributions: readonly DossierContribution[];
  earned: number;
  available: number;
  band: string;
  score: number;
  /** Every band and its number — the whole ruler. */
  scale: readonly (readonly [string, number])[];
  /** Points the next band up needs. Null at the top band. */
  required: number | null;
  /** Every readable factor scored and the band still fell short: capped
      by what could be read, not by the company. */
  cappedByUnreadableFactors: boolean;
  /** The arithmetic as one line, worded by the backend. */
  stated: string;
  /** How much of what the score asks for could be read. A different
      question from how much of what was read was favourable. */
  establishedFactors: number | null;
  candidateFactors: number | null;
  /** The same, worded by the backend. Never composed here. */
  coverage: string | null;
}

export interface DossierScore {
  value: number | null;
  /** What this score is called on this dossier — "Business quality" on an
      equity, "Asset quality" on a token. Worded by the backend's dossier
      definition; this side never chooses a score's name. */
  label: string;
  basis: string;
  evidence: readonly string[];
  /** "measurement" | "policy" | "assessment" — the backend's own word. */
  kind: string;
  /** The same, worded for a reader. Never composed on this side. */
  kindStated: string;
  /** The arithmetic beneath the number, where the score counted factors. */
  derivation: DossierDerivation | null;
}

/**
 * Every score runs the same way: a higher number is better for the case.
 *
 * Risk arrives as safety for that reason — the same reading, turned once
 * by the backend, so the set can be compared or averaged without one
 * dimension quietly meaning the opposite of the others.
 */
export interface DossierScores {
  quality: DossierScore;
  evidence: DossierScore;
  valuation: DossierScore;
  safety: DossierScore;
  portfolioFit: DossierScore;
}

export interface NarrativeFinding {
  id: string;
  statement: string;
  source: string;
}

export interface NarrativeSection {
  section: string;
  text: string;
  findingIds: readonly string[];
}

/**
 * The case in institutional language — communication only.
 *
 * Written by the Executive Writer from the canonical objects; every
 * section cites the findings it rests on, and the recommendation is a
 * backend-validated echo of the decision. The structured dossier remains
 * canonical; this is language on top of a finished judgment.
 */
export interface DossierNarrative {
  headline: string;
  recommendation: string;
  sections: readonly NarrativeSection[];
  findings: readonly NarrativeFinding[];
  model: string;
  written: string;
}

export interface PlaybookCoverage {
  analyst: string;
  label: string;
  covered: boolean;
  /** Why it was not asked. Null where it was. */
  reason: string | null;
}

/**
 * The framework this security is read with, and what it covers.
 *
 * A sector says what a company sells. This says how it is read, which is
 * what actually determines the analysis — and therefore what a reader
 * needs in order to understand why one dossier looks unlike another.
 */
export interface DossierRatingDimension {
  label: string;
  score: number;
}

/**
 * A named third party's published rating of a token.
 *
 * Carried under their name and rendered with a link to their own page,
 * because it is their opinion and not this platform's judgement. It
 * reaches no score and no decision — the Yahoo boundary applied to an
 * opinion instead of a label.
 */
export interface DossierTokenRating {
  source: string;
  name: string;
  level: string;
  score: number;
  dimensions: readonly DossierRatingDimension[];
  /** When the rater last reviewed it, which is the date that matters. */
  reviewedAt: string | null;
  pageUrl: string | null;
  reportUrl: string | null;
  read: DossierProvenance | null;
}

/**
 * What owning the fund costs, as the provider reports it.
 *
 * An evidenced fact about the wrapper, never a judgement: the backend
 * words the sentence and this surface renders it. It reaches no score
 * and no decision.
 */
export interface DossierFundCost {
  /** The backend's own sentence. Rendered verbatim, never reworded. */
  stated: string;
  /** Decimal ratio of assets per year: 0.0007 is 0.07%. */
  expenseRatio: number;
  read: DossierProvenance | null;
}

export interface DossierPlaybook {
  kind: string;
  name: string;
  explanation: string;
  priorities: readonly string[];
  coverage: readonly PlaybookCoverage[];
  /** False when no industry was reported, so nothing was chosen on evidence. */
  classified: boolean;
}

/**
 * Where the market files this company — context, never a conclusion.
 *
 * The provider's own category strings, dated. Both absences arrive
 * worded by the backend: a profile that names no industry and a profile
 * never acquired are different facts, and this side renders whichever
 * sentence it was sent.
 */
export interface DossierIndustryContext {
  /** The one line printed large: the industry, or the backend's absence word. */
  label: string;
  industry: string | null;
  sector: string | null;
  /** The backend's own sentence for this state. Rendered verbatim. */
  stated: string;
  /** When this platform read it. Null where no profile was ever acquired. */
  read: DossierProvenance | null;
}

/**
 * The investment playbook MOVRvest established, or the honest state.
 *
 * Exactly one of three backend-declared states — established, refused,
 * unavailable — each carrying the owning layer's sentence. This side
 * renders the state it was given and classifies nothing: no industry
 * string, default or fallback prose can turn an absence into a playbook.
 */
export interface DossierEarnedPlaybook {
  /** "established" | "refused" | "unavailable" — the backend's word. */
  state: string;
  /** The playbook's name, only where established. Never a default. */
  playbook: string | null;
  /** The one line printed large: the playbook name, or the state word. */
  label: string;
  /** The owning layer's sentence, verbatim. */
  stated: string;
  /** What the conclusion rests on, worded with its count. */
  narrowestAgreement: string | null;
}

/**
 * One time the Artificial CIO changed its mind, and what moved under it.
 *
 * Every sentence arrives from the backend: the change itself, the
 * rationale it recorded at the time, and each score that differed. This
 * side computes no delta — a score that stopped being measurable is a
 * different fact from one that fell, and only the domain may say which.
 */
export interface DossierTransition {
  at: string;
  fromState: string;
  toState: string;
  /** Either side may be absent, and an absent conviction is not a low one. */
  fromConviction: number | null;
  toConviction: number | null;
  /** The change in one line, worded by the backend. */
  stated: string;
  /** The rationale the CIO recorded at the time, verbatim. */
  rationale: string;
  /** Each score that differed, worded. Empty where `unexplained`. */
  moved: readonly string[];
  /** True where a record predates the journal keeping scores, so an
      empty `moved` means "cannot be said" rather than "nothing moved". */
  unexplained: boolean;
}

/**
 * Every recorded change of mind about this security.
 *
 * It reports what was recorded and judges none of it — whether those
 * decisions were right is the track record's question.
 */
export interface DossierDecisionCourse {
  reviews: number;
  changes: number;
  firstRecordedAt: string | null;
  lastRecordedAt: string | null;
  /** Most recent first. */
  transitions: readonly DossierTransition[];
  /** The course in one sentence, worded by the backend. Null where there
      is no course to state — `absentBecause` carries the reason, and the
      two are mutually exclusive by construction. */
  stated: string | null;
  /** Why there is no course — a first review has nothing to have
      changed from. Null where there is one. */
  absentBecause: string | null;
}

/**
 * Industry beside the earned playbook — two classifications, two
 * questions, never blended and never substituted for each other.
 */
export interface DossierClassification {
  industry: DossierIndustryContext;
  playbook: DossierEarnedPlaybook;
  /** The backend's sentence separating the two concepts. */
  distinction: string;
}

/**
 * What kind of investment case this dossier is, declared by the backend.
 *
 * The asset-specific definition beneath the shared shell: an equity and a
 * crypto dossier differ because the domain says so. This side renders
 * these strings and decides nothing — it does not infer an asset class,
 * reinterpret a metric, or choose which sections apply.
 */
export interface DossierDefinition {
  /** "equity" | "crypto" | "general" — the backend's own word. */
  kind: string;
  /** What the case is called at the top of the page. */
  title: string;
  /** The heading over the classification section — industry beside the
      earned playbook. A token has an asset type instead. */
  classificationHeading: string;
  /** The heading over the analysis-framework card, worded as what it
      is, so an industry-chosen frame never reads as a classification. */
  analysisHeading: string;
  /** False where the subject publishes no filings — a property of the
      asset class, never unread work. The understanding sections are then
      not sent at all, and the reason is here. */
  filingsApply: boolean;
  filingsInapplicableBecause: string | null;
}

export interface DossierViewModel {
  symbol: string;

  /** The dossier's own semantics: title, headings, which sections belong. */
  definition: DossierDefinition;

  decisionState: string;
  /** Null where the CIO withheld one — never rendered as a zero. */
  conviction: number | null;
  /** Null with it: there is no word for a number nobody put on the case. */
  convictionLabel: string | null;
  /** Null where no committee could form a view — not disagreement. */
  committeeAgreement: number | null;
  rationale: string;
  /** Null when the CIO has no recorded history for this symbol. */
  trend: DecisionTrendViewModel | null;
  action: ExecutiveActionViewModel | null;
  convictionChange: ConvictionChangeViewModel | null;

  /** Every recorded change of mind about this security, with the
      rationale recorded at the time. Null only where the backend
      predates the field. */
  decisionCourse: DossierDecisionCourse | null;
  playbook: DossierPlaybook | null;

  /** Industry beside the earned playbook, each in its honest state.
      Null where the subject is not a company. */
  classification: DossierClassification | null;

  summary: string;
  expectedHoldingPeriod: string;
  catalysts: readonly string[];
  invalidationConditions: readonly string[];
  nextTrigger: string | null;

  /** False when nothing about the security itself could be gathered. */
  securityEvidenced: boolean;
  evidenceWeighed: readonly string[];
  strengths: readonly string[];
  risks: readonly string[];
  missingEvidence: readonly string[];
  scores: DossierScores;

  /** Facts about the account and market — kept apart from the security. */
  contextStrengths: readonly string[];
  contextRisks: readonly string[];

  committees: readonly DossierCommitteeOpinion[];

  /** When the security's evidence was read. Null where none was. */
  evidenceAsOf: DossierProvenance | null;

  /** Somebody else's rating of this token. Beside the case, never in it. */
  tokenRating: DossierTokenRating | null;

  /** What owning the fund costs, dated. Null for anything not a fund. */
  fundCost: DossierFundCost | null;

  /** The token's judged market facts. Null for anything not a crypto asset. */
  assetProfile: DossierAssetProfile | null;

  /** The economics of the system behind the token. Its own evidence
      family, independent of the market facts and consumed by nothing. */
  protocolFundamentals: DossierProtocolFundamentals | null;

  /** Which investment questions this kind of digital asset is asked,
      which are declined and why, and what evidence would answer each.
      Applicability and evidence standing, never a verdict. */
  cryptoPlaybook: DossierCryptoPlaybook | null;

  /** What kind of crypto market this asset is trading inside, and its
      place in it. Market context — never Asset Quality. */
  cryptoMarket: DossierCryptoMarket | null;

  /** What each of this token's supply numbers actually counts. */
  supply: DossierSupply | null;

  /** The narrative, or null with the backend-worded reason beside it. */
  narrative: DossierNarrative | null;
  narrativeAbsent: string | null;

  /**
   * What the platform understands about the company from its own filing.
   *
   * Beside the case, never inside it: nothing here reached the decision
   * above. Null only when the backend predates the field.
   */
  understanding: DossierUnderstanding | null;

  /**
   * The conclusion as because / despite / review if.
   *
   * Where `rationale` says which gate the case reached, this says what
   * the decision rests on and what would occasion a second look. Null
   * only when the backend predates the field.
   */
  synthesis: DossierSynthesis | null;
}

/** One fact in the conclusion, and how far it goes. */
export interface DossierSynthesisFact {
  statement: string;
  /** "established" — from the filing, checked. "assessed" — an analyst. */
  origin: string;
  /** Which committee stood on it. Null where no remit covers it. */
  committee: string | null;
}

/** One thing a named committee could not settle. */
export interface DossierUncertainty {
  committee: string;
  kind: string;
  about: string;
  resolvable: boolean;
}

/** Why this conclusion prevailed over the one that did not. */
export interface DossierDeliberation {
  agreement: string;
  prevailed: string;
  /** The position that did not carry. Null where none contradicted it. */
  over: string | null;
  because: string;
}

/** A named condition for looking at the decision again. */
export interface DossierReviewCondition {
  condition: string;
  origin: string;
  /** What it would change. Null where it names a gap, not an alternative. */
  wouldChange: string | null;
}

export interface DossierSynthesis {
  state: string;
  /** Null where the CIO withheld one, carried through unchanged. */
  conviction: number | null;
  because: readonly DossierSynthesisFact[];
  becauseAbsent: string | null;
  despite: readonly DossierSynthesisFact[];
  despiteAbsent: string | null;
  reviewIf: readonly DossierReviewCondition[];
  reviewIfAbsent: string | null;
  /** What is not yet known — its own part, never a reason against. */
  uncertainty: readonly DossierUncertainty[];
  uncertaintyAbsent: string | null;
  /** Why the positives outweigh the negatives, or the reverse. */
  deliberation: DossierDeliberation | null;
  /** What the filing establishes — carried, and not consumed by the decision. */
  established: readonly DossierSynthesisFact[];
  /** Whether the investor is given anything to disagree with. */
  challengeable: boolean;
  /** Whether the conclusion shows an argument rather than a checklist. */
  deliberated: boolean;
}

/** How firmly one claim is held, as the readings counted. */
export interface DossierAgreement {
  agreeing: number;
  readings: number;
  settled: boolean;
}

/** One part of the business, as the filing's consensus establishes it. */
export interface DossierSegment {
  name: string;
  /** The settled share of revenue. Null with the reason beside it. */
  share: number | null;
  unmeasuredBecause: string | null;
  earns: readonly string[];
  earnsBecause: string | null;
  /** The filer's stated economic dependence of this business on
      another, worded by the backend with the filer's own degree
      intact. Null is an evidence state, never independence. */
  depends: string | null;
  dependsQuoted: string | null;
  dependsSupport: string | null;
}

/** One way the business earns, and how much of it earns that way. */
export interface DossierMechanism {
  model: string;
  through: readonly string[];
  /** Coverage of measured revenue — never a split of revenue. */
  coverage: number | null;
  support: DossierAgreement;
}

/** One thing the rules needed about a segment and did not have. */
export interface DossierUnestablished {
  segment: string;
  dimension: string;
  because: string;
}

export interface DossierBusinessUnderstanding {
  source: string;
  read: string;
  quorate: boolean;
  observationCount: number;
  quorum: number;
  engine: string;
  archetype: string | null;
  undecidedBecause: string | null;
  /** The narrowest claim beneath the conclusion. */
  narrowest: DossierAgreement | null;
  segments: readonly DossierSegment[];
  segmentsBecause: string | null;
  mechanisms: readonly DossierMechanism[];
  notEstablished: readonly DossierUnestablished[];
}

/** One measure, computed from checked cells or absent with its reason. */
export interface DossierMeasure {
  measure: string;
  label: string;
  value: number | null;
  /** "fraction", "multiple" or "currency" — how to read the number. */
  unit: string;
  /** The arithmetic, as it can be checked against the filing. */
  stated: string;
  support: DossierAgreement | null;
  absentBecause: string | null;
}

export interface DossierFinancialUnderstanding {
  source: string;
  read: string;
  quorate: boolean;
  observationCount: number;
  quorum: number;
  statements: readonly string[];
  /** The financial language the income statement establishes. */
  language: string | null;
  languageBecause: string | null;
  measures: readonly DossierMeasure[];
}

export interface DossierUnderstanding {
  business: DossierBusinessUnderstanding | null;
  businessAbsentBecause: string | null;
  financial: DossierFinancialUnderstanding | null;
  financialAbsentBecause: string | null;
}

/**
 * One market fact about a token, with its standing beside it.
 *
 * The standing is the trust label: an established fact, a provider
 * claim nothing could corroborate, MOVRvest's own arithmetic over
 * established inputs, or a worded absence. All worded by the backend —
 * this side styles a chip and prints strings.
 */
export interface TokenFactRow {
  label: string;
  /** The value already worded — "$18.3bn" — or null with the reason. */
  stated: string | null;
  /** "established" | "claimed" | "rejected" | "absent" | "calculated" */
  standing: string;
  /** The same, worded by the backend. */
  standingStated: string;
  source: string | null;
  age: string | null;
  because: string | null;
}

export interface TokenFactGroup {
  title: string;
  rows: readonly TokenFactRow[];
}

/**
 * What is measured about this asset, judged before it is served — and
 * the claims that failed validation, disclosed rather than discarded.
 */
export interface DossierAssetProfile {
  groups: readonly TokenFactGroup[];
  rejected: readonly string[];
}

/**
 * One figure about the economic system behind a token.
 *
 * Availability and standing answer different questions and are shown
 * apart: "not applicable" is not a gap, and a provider claim is not an
 * established fact. Both words are the backend's.
 */
export interface ProtocolFactRow {
  metric: string;
  label: string;
  /** capital | activity | value_generation | holder_accrual */
  family: string;
  stated: string | null;
  /** The window the figure covers, or null for a level. */
  window: string | null;
  standing: string;
  standingStated: string;
  availability: string;
  availabilityStated: string;
  source: string | null;
  age: string | null;
  /** The provider's own definition, verbatim — the mechanism itself. */
  providerMethodology: string | null;
  because: string | null;
}

export interface ProtocolEntityView {
  key: string;
  name: string;
  /** "chain" or "protocol". */
  kind: string;
  measures: string;
  mappingBasis: string;
  mappingSettled: boolean;
  facts: readonly ProtocolFactRow[];
}

export interface DerivedFigureView {
  label: string;
  statedValue: string;
  stated: string;
  caveat: string;
}

/** The economics behind a token — evidence, never conclusions. */
export interface DossierProtocolFundamentals {
  entities: readonly ProtocolEntityView[];
  derived: readonly DerivedFigureView[];
  unmappedBecause: string | null;
}

export interface AnalyticalCapabilityView {
  key: string;
  label: string;
  reads: string;
}

export interface ConsideredArchetypeView {
  archetype: string;
  notChosenBecause: string;
}

/** One evidence demand of one question, met or unmet. */
export interface QuestionEvidenceView {
  demand: string;
  met: boolean;
  stated: string | null;
  standing: string;
  standingStated: string;
  source: string | null;
  age: string | null;
  /** Which economic entity supplied it, where more than one exists. */
  entity: string | null;
  because: string | null;
}

/**
 * One investment question against one token.
 *
 * `cell` is the product of two independent facts and never a third
 * judgment: whether the question applies to this kind of asset (decided
 * from the archetype, with no figure consulted) and whether anything
 * established answers it (decided from the evidence, with no opinion of
 * the question consulted).
 */
export interface CryptoQuestionView {
  key: string;
  label: string;
  asks: string;
  mattersBecause: string;
  /** ask | ask_evidence_insufficient | not_applicable | undetermined */
  cell: string;
  cellStated: string;
  applicability: string;
  applicabilityBecause: string;
  askedBy: string | null;
  bestStanding: string;
  bestStandingStated: string;
  evidence: readonly QuestionEvidenceView[];
}

export interface ValueChainLinkView {
  stage: string;
  label: string;
  stated: string | null;
  window: string | null;
  standing: string;
  standingStated: string;
  availabilityStated: string;
  /** The source's own definition, verbatim. */
  methodology: string | null;
  because: string | null;
}

/** How one entity's value moves, from use to the token. */
export interface ValueChainView {
  entity: string;
  kind: string;
  measures: string;
  mappingSettled: boolean;
  links: readonly ValueChainLinkView[];
  mechanism: string;
  mechanismStated: string;
  mechanismSourceWording: string | null;
  because: string;
}

/**
 * Which investment questions this kind of digital asset is asked.
 *
 * Applicability, evidence demands and evidence standing — never a
 * verdict. Nothing here is scored, banded or ranked.
 */
export interface DossierCryptoPlaybook {
  archetype: string;
  name: string;
  explanation: string;
  confidence: string;
  confidenceStated: string;
  because: string;
  restsOn: readonly string[];
  doesNotEstablish: readonly string[];
  alternatives: readonly ConsideredArchetypeView[];
  notClassifiedFrom: readonly string[];
  capabilities: readonly AnalyticalCapabilityView[];
  unmodelled: readonly string[];
  questions: readonly CryptoQuestionView[];
  chains: readonly ValueChainView[];
  unmappedBecause: string | null;
}


/** One market figure, with its interval and the universe behind it. */
export interface MarketObservationView {
  metric: string;
  label: string;
  /** What it covers in time. Never generalised into a "trend". */
  interval: string;
  intervalStated: string;
  stated: string | null;
  standing: string;
  standingStated: string;
  /** True where MOVRvest computed it rather than read it. */
  derived: boolean;
  universe: string | null;
  source: string | null;
  age: string | null;
  because: string | null;
}

export interface RelativeReturnView {
  interval: string;
  comparator: string;
  subjectReturn: string;
  comparatorReturn: string;
  delta: string;
  standing: string;
  stated: string;
  caveat: string | null;
}

export interface ConcentrationView {
  comparator: string;
  stated: string;
}

/**
 * The externally observed group this asset is compared against.
 *
 * A vendor's category under the vendor's name. It is NOT the analytical
 * archetype and never modifies one — an asset read as a smart-contract
 * network can sit in a market group containing Bitcoin.
 */
export interface PeerGroupView {
  key: string;
  name: string;
  provider: string;
  selectedBecause: string;
  caveats: readonly string[];
}

export interface ConsideredPeerGroupView {
  name: string;
  rejectedBecause: string;
}

/** Market context — never Asset Quality. Nothing here is banded or scored. */
export interface DossierCryptoMarket {
  market: readonly MarketObservationView[];
  marketSource: string | null;
  marketAge: string | null;
  returns: readonly MarketObservationView[];
  peer: PeerGroupView | null;
  peerUnavailableBecause: string | null;
  considered: readonly ConsideredPeerGroupView[];
  peerObservations: readonly MarketObservationView[];
  relative: readonly RelativeReturnView[];
  concentrations: readonly ConcentrationView[];
  uncompared: readonly string[];
  unavailableBecause: string | null;
}


/** One supply quantity, under one concept and one methodology. */
export interface SupplyFigureView {
  concept: string;
  conceptStated: string;
  stated: string;
  /** Whose definition decided what is in the number. */
  definedBy: string;
  methodology: string;
  /** Whether the platform knows what the definition leaves out. */
  disclosed: boolean;
  excludes: readonly string[];
  source: string;
  age: string | null;
  reportedAs: string | null;
  standing: string;
  standingStated: string;
  authority: string;
  authorityStated: string;
  because: string | null;
  caveats: readonly string[];
}

/**
 * What two supply figures are to each other.
 *
 * `coexist` is the state this layer exists to make possible: two numbers
 * that differ because they count different things — information, not a
 * contradiction.
 */
export interface SupplyComparisonView {
  verdict: string;
  verdictStated: string;
  leftSource: string;
  leftStated: string;
  rightSource: string;
  rightStated: string;
  because: string;
}

/** A token's supply as a vocabulary. No dilution reading, no band. */
export interface DossierSupply {
  figures: readonly SupplyFigureView[];
  comparisons: readonly SupplyComparisonView[];
  methodologyDisagreement: boolean;
  unresolved: readonly string[];
  unavailableBecause: string | null;
}

export interface DossierResult {
  /** Null when the backend was unreachable — nothing stands in. */
  dossier: DossierViewModel | null;
  source: "backend" | "unavailable";
  backendUrl: string;
  error?: string;
}

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`Expected a string at "${field}", received ${typeof value}`);
  }

  return value;
}

function optionalString(value: unknown, field: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value !== "string") {
    throw new Error(
      `Expected a string or null at "${field}", received ${typeof value}`,
    );
  }

  return value.trim().length === 0 ? null : value;
}

function requireNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`Expected a number at "${field}", received ${typeof value}`);
  }

  return value;
}

/** A number the platform may not have been able to measure. */
function optionalNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function requireBoolean(value: unknown, field: string): boolean {
  if (typeof value !== "boolean") {
    throw new Error(
      `Expected a boolean at "${field}", received ${typeof value}`,
    );
  }

  return value;
}

function stringList(value: unknown): readonly string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

/**
 * One score with its reasoning, or a refusal to render it half-formed.
 *
 * A score arriving without its basis would be exactly the bare figure the
 * basis exists to prevent, so it is an error rather than a silent blank.
 */
function parseScore(value: unknown, field: string): DossierScore {
  if (!isRecord(value)) {
    throw new Error(`Expected a score object at "${field}".`);
  }

  return {
    value: optionalNumber(value.value),
    label: requireString(value.label, `${field}.label`),
    basis: requireString(value.basis, `${field}.basis`),
    evidence: stringList(value.evidence),
    kind: requireString(value.kind, `${field}.kind`),
    kindStated: requireString(value.kind_stated, `${field}.kind_stated`),
    derivation: parseDerivation(value.derivation, `${field}.derivation`),
  };
}

/**
 * The dossier's declared semantics, or a refusal to render without them.
 *
 * Required, not defaulted: a page that fell back to company wording when
 * the definition was missing would be this side deciding the asset class
 * — the exact inference this contract exists to remove.
 */
function parseDefinition(value: unknown): DossierDefinition {
  if (!isRecord(value)) {
    throw new Error("The dossier response has no definition object.");
  }

  return {
    kind: requireString(value.kind, "definition.kind"),
    title: requireString(value.title, "definition.title"),
    classificationHeading: requireString(
      value.classification_heading,
      "definition.classification_heading",
    ),
    analysisHeading: requireString(
      value.analysis_heading,
      "definition.analysis_heading",
    ),
    filingsApply: requireBoolean(
      value.filings_apply,
      "definition.filings_apply",
    ),
    filingsInapplicableBecause: optionalString(
      value.filings_inapplicable_because,
      "definition.filings_inapplicable_because",
    ),
  };
}

function parseDerivation(
  value: unknown,
  field: string,
): DossierDerivation | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error(`Expected a derivation object at "${field}".`);
  }

  const contributions = Array.isArray(value.contributions)
    ? value.contributions
    : [];

  const scale = Array.isArray(value.scale) ? value.scale : [];

  return {
    contributions: contributions.filter(isRecord).map((item, index) => ({
      statement: requireString(
        item.statement,
        `${field}.contributions[${index}].statement`,
      ),
      points: requireNumber(
        item.points,
        `${field}.contributions[${index}].points`,
      ),
      sense: requireString(
        item.sense,
        `${field}.contributions[${index}].sense`,
      ),
      verdict: optionalString(
        item.verdict,
        `${field}.contributions[${index}].verdict`,
      ),
    })),
    earned: requireNumber(value.earned, `${field}.earned`),
    available: requireNumber(value.available, `${field}.available`),
    band: requireString(value.band, `${field}.band`),
    score: requireNumber(value.score, `${field}.score`),
    scale: scale
      .filter((row): row is [string, number] => Array.isArray(row))
      .map((row) => [String(row[0]), Number(row[1])] as const),
    required: optionalNumber(value.required),
    cappedByUnreadableFactors: value.capped_by_unreadable_factors === true,
    stated: requireString(value.stated, `${field}.stated`),
    establishedFactors: optionalNumber(value.established_factors),
    candidateFactors: optionalNumber(value.candidate_factors),
    coverage: optionalString(value.coverage, `${field}.coverage`),
  };
}

function parseProvenance(
  value: unknown,
  field: string,
): DossierProvenance | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error(`Expected an object or null at "${field}".`);
  }

  return {
    source: requireString(value.source, `${field}.source`),
    age: requireString(value.age, `${field}.age`),
    lastKnown: value.last_known === true,
  };
}

function parseTokenRating(value: unknown): DossierTokenRating | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "token_rating".');
  }

  const dimensions = Array.isArray(value.dimensions) ? value.dimensions : [];

  return {
    source: requireString(value.source, "token_rating.source"),
    name: requireString(value.name, "token_rating.name"),
    level: requireString(value.level, "token_rating.level"),
    score: typeof value.score === "number" ? value.score : 0,
    dimensions: dimensions.flatMap((item) =>
      isRecord(item) &&
      typeof item.label === "string" &&
      typeof item.score === "number"
        ? [{ label: item.label, score: item.score }]
        : [],
    ),
    reviewedAt: optionalString(value.reviewed_at, "token_rating.reviewed_at"),
    pageUrl: optionalString(value.page_url, "token_rating.page_url"),
    reportUrl: optionalString(value.report_url, "token_rating.report_url"),
    read: parseProvenance(value.read, "token_rating.read"),
  };
}

function parseDecisionCourse(value: unknown): DossierDecisionCourse | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "decision_course".');
  }

  const transitions = Array.isArray(value.transitions) ? value.transitions : [];

  return {
    reviews: requireNumber(value.reviews, "decision_course.reviews"),
    changes: requireNumber(value.changes, "decision_course.changes"),
    firstRecordedAt: optionalString(
      value.first_recorded_at,
      "decision_course.first_recorded_at",
    ),
    lastRecordedAt: optionalString(
      value.last_recorded_at,
      "decision_course.last_recorded_at",
    ),
    transitions: transitions.filter(isRecord).map((item, index) => ({
      at: requireString(item.at, `decision_course.transitions[${index}].at`),
      fromState: requireString(
        item.from_state,
        `decision_course.transitions[${index}].from_state`,
      ),
      toState: requireString(
        item.to_state,
        `decision_course.transitions[${index}].to_state`,
      ),
      // Either side may be absent. `stated` below is the backend's own
      // sentence and already leaves the conviction clause out where it is.
      fromConviction: optionalNumber(item.from_conviction),
      toConviction: optionalNumber(item.to_conviction),
      // The backend's own sentences are required, never defaulted: a
      // transition without them is exactly what this section must not
      // invent.
      stated: requireString(
        item.stated,
        `decision_course.transitions[${index}].stated`,
      ),
      rationale: requireString(
        item.rationale,
        `decision_course.transitions[${index}].rationale`,
      ),
      moved: stringList(item.moved),
      unexplained: item.unexplained === true,
    })),
    // The backend sends "" — not null — where there is no course to
    // state, and `requireString` rejects an empty string. So a security
    // with exactly one recorded review threw here, and the whole dossier
    // rendered "the backend is unreachable" over a payload that had
    // arrived intact. Found by DV2 on UNP; the sentence it belongs with
    // is `absent_because`, which was populated the whole time.
    stated: optionalString(value.stated, "decision_course.stated"),
    absentBecause: optionalString(
      value.absent_because,
      "decision_course.absent_because",
    ),
  };
}

const EARNED_PLAYBOOK_STATES = new Set(["established", "refused", "unavailable"]);

function parseClassification(value: unknown): DossierClassification | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "classification".');
  }

  const industry = value.industry;

  if (!isRecord(industry)) {
    throw new Error('Expected an object at "classification.industry".');
  }

  const playbook = value.playbook;

  if (!isRecord(playbook)) {
    throw new Error('Expected an object at "classification.playbook".');
  }

  const state = requireString(playbook.state, "classification.playbook.state");

  // A state this side does not know is refused, not defaulted: rendering
  // an unknown state with borrowed wording is how a fallback playbook
  // would sneak back in.
  if (!EARNED_PLAYBOOK_STATES.has(state)) {
    throw new Error(
      `Unknown earned-playbook state "${state}" at "classification.playbook.state".`,
    );
  }

  return {
    industry: {
      label: requireString(industry.label, "classification.industry.label"),
      industry: optionalString(
        industry.industry,
        "classification.industry.industry",
      ),
      sector: optionalString(industry.sector, "classification.industry.sector"),
      // The backend's sentence is required, not defaulted: an industry
      // string without its worded standing is exactly what this section
      // exists to end.
      stated: requireString(industry.stated, "classification.industry.stated"),
      read: parseProvenance(industry.read, "classification.industry.read"),
    },
    playbook: {
      state,
      playbook: optionalString(
        playbook.playbook,
        "classification.playbook.playbook",
      ),
      label: requireString(playbook.label, "classification.playbook.label"),
      stated: requireString(playbook.stated, "classification.playbook.stated"),
      narrowestAgreement: optionalString(
        playbook.narrowest_agreement,
        "classification.playbook.narrowest_agreement",
      ),
    },
    distinction: requireString(value.distinction, "classification.distinction"),
  };
}

function parseFundCost(value: unknown): DossierFundCost | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "fund_cost".');
  }

  if (typeof value.expense_ratio !== "number") {
    throw new Error('Expected a number at "fund_cost.expense_ratio".');
  }

  return {
    // The backend's sentence is required, not defaulted: a figure
    // without its worded meaning is exactly what this surface must
    // never invent.
    stated: requireString(value.stated, "fund_cost.stated"),
    expenseRatio: value.expense_ratio,
    read: parseProvenance(value.read, "fund_cost.read"),
  };
}

function parseAssetProfile(value: unknown): DossierAssetProfile | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "asset_profile".');
  }

  const groups = Array.isArray(value.groups) ? value.groups : [];
  const rejected = Array.isArray(value.rejected) ? value.rejected : [];

  return {
    groups: groups.filter(isRecord).map((group, index) => ({
      title: requireString(group.title, `asset_profile.groups[${index}].title`),
      rows: (Array.isArray(group.rows) ? group.rows : [])
        .filter(isRecord)
        .map((row, rowIndex) => {
          const field = `asset_profile.groups[${index}].rows[${rowIndex}]`;

          return {
            label: requireString(row.label, `${field}.label`),
            stated: optionalString(row.stated, `${field}.stated`),
            standing: requireString(row.standing, `${field}.standing`),
            standingStated: requireString(
              row.standing_stated,
              `${field}.standing_stated`,
            ),
            source: optionalString(row.source, `${field}.source`),
            age: optionalString(row.age, `${field}.age`),
            because: optionalString(row.because, `${field}.because`),
          };
        }),
    })),
    rejected: rejected
      .filter(isRecord)
      .map((item, index) =>
        requireString(item.statement, `asset_profile.rejected[${index}].statement`),
      ),
  };
}

function parseProtocolFundamentals(
  value: unknown,
): DossierProtocolFundamentals | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "protocol_fundamentals".');
  }

  const entities = Array.isArray(value.entities) ? value.entities : [];
  const derived = Array.isArray(value.derived) ? value.derived : [];

  return {
    entities: entities.filter(isRecord).map((entity, index) => {
      const field = `protocol_fundamentals.entities[${index}]`;

      return {
        key: requireString(entity.key, `${field}.key`),
        name: requireString(entity.name, `${field}.name`),
        kind: requireString(entity.kind, `${field}.kind`),
        measures: requireString(entity.measures, `${field}.measures`),
        mappingBasis: requireString(
          entity.mapping_basis,
          `${field}.mapping_basis`,
        ),
        mappingSettled: entity.mapping_settled === true,
        facts: (Array.isArray(entity.facts) ? entity.facts : [])
          .filter(isRecord)
          .map((fact, factIndex) => {
            const row = `${field}.facts[${factIndex}]`;

            return {
              metric: requireString(fact.metric, `${row}.metric`),
              label: requireString(fact.label, `${row}.label`),
              family: requireString(fact.family, `${row}.family`),
              stated: optionalString(fact.stated, `${row}.stated`),
              window: optionalString(fact.window, `${row}.window`),
              standing: requireString(fact.standing, `${row}.standing`),
              standingStated: requireString(
                fact.standing_stated,
                `${row}.standing_stated`,
              ),
              availability: requireString(
                fact.availability,
                `${row}.availability`,
              ),
              availabilityStated: requireString(
                fact.availability_stated,
                `${row}.availability_stated`,
              ),
              source: optionalString(fact.source, `${row}.source`),
              age: optionalString(fact.age, `${row}.age`),
              providerMethodology: optionalString(
                fact.provider_methodology,
                `${row}.provider_methodology`,
              ),
              because: optionalString(fact.because, `${row}.because`),
            };
          }),
      };
    }),
    derived: derived.filter(isRecord).map((figure, index) => {
      const field = `protocol_fundamentals.derived[${index}]`;

      return {
        label: requireString(figure.label, `${field}.label`),
        statedValue: requireString(figure.stated_value, `${field}.stated_value`),
        stated: requireString(figure.stated, `${field}.stated`),
        caveat: requireString(figure.caveat, `${field}.caveat`),
      };
    }),
    unmappedBecause: optionalString(
      value.unmapped_because,
      "protocol_fundamentals.unmapped_because",
    ),
  };
}

function parseCryptoPlaybook(value: unknown): DossierCryptoPlaybook | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "crypto_playbook".');
  }

  const strings = (raw: unknown): readonly string[] =>
    (Array.isArray(raw) ? raw : []).filter(
      (item): item is string => typeof item === "string",
    );

  return {
    archetype: requireString(value.archetype, "crypto_playbook.archetype"),
    name: requireString(value.name, "crypto_playbook.name"),
    explanation: requireString(value.explanation, "crypto_playbook.explanation"),
    confidence: requireString(value.confidence, "crypto_playbook.confidence"),
    confidenceStated: requireString(
      value.confidence_stated,
      "crypto_playbook.confidence_stated",
    ),
    because: requireString(value.because, "crypto_playbook.because"),
    restsOn: strings(value.rests_on),
    doesNotEstablish: strings(value.does_not_establish),
    alternatives: (Array.isArray(value.alternatives) ? value.alternatives : [])
      .filter(isRecord)
      .map((alternative, index) => ({
        archetype: requireString(
          alternative.archetype,
          `crypto_playbook.alternatives[${index}].archetype`,
        ),
        notChosenBecause: requireString(
          alternative.not_chosen_because,
          `crypto_playbook.alternatives[${index}].not_chosen_because`,
        ),
      })),
    notClassifiedFrom: strings(value.not_classified_from),
    capabilities: (Array.isArray(value.capabilities) ? value.capabilities : [])
      .filter(isRecord)
      .map((capability, index) => ({
        key: requireString(
          capability.key,
          `crypto_playbook.capabilities[${index}].key`,
        ),
        label: requireString(
          capability.label,
          `crypto_playbook.capabilities[${index}].label`,
        ),
        reads: requireString(
          capability.reads,
          `crypto_playbook.capabilities[${index}].reads`,
        ),
      })),
    unmodelled: strings(value.unmodelled),
    questions: (Array.isArray(value.questions) ? value.questions : [])
      .filter(isRecord)
      .map((question, index) => {
        const field = `crypto_playbook.questions[${index}]`;

        return {
          key: requireString(question.key, `${field}.key`),
          label: requireString(question.label, `${field}.label`),
          asks: requireString(question.asks, `${field}.asks`),
          mattersBecause: requireString(
            question.matters_because,
            `${field}.matters_because`,
          ),
          cell: requireString(question.cell, `${field}.cell`),
          cellStated: requireString(question.cell_stated, `${field}.cell_stated`),
          applicability: requireString(
            question.applicability,
            `${field}.applicability`,
          ),
          applicabilityBecause: requireString(
            question.applicability_because,
            `${field}.applicability_because`,
          ),
          askedBy: optionalString(question.asked_by, `${field}.asked_by`),
          bestStanding: requireString(
            question.best_standing,
            `${field}.best_standing`,
          ),
          bestStandingStated: requireString(
            question.best_standing_stated,
            `${field}.best_standing_stated`,
          ),
          evidence: (Array.isArray(question.evidence) ? question.evidence : [])
            .filter(isRecord)
            .map((item, itemIndex) => {
              const row = `${field}.evidence[${itemIndex}]`;

              return {
                demand: requireString(item.demand, `${row}.demand`),
                met: item.met === true,
                stated: optionalString(item.stated, `${row}.stated`),
                standing: requireString(item.standing, `${row}.standing`),
                standingStated: requireString(
                  item.standing_stated,
                  `${row}.standing_stated`,
                ),
                source: optionalString(item.source, `${row}.source`),
                age: optionalString(item.age, `${row}.age`),
                entity: optionalString(item.entity, `${row}.entity`),
                because: optionalString(item.because, `${row}.because`),
              };
            }),
        };
      }),
    chains: (Array.isArray(value.chains) ? value.chains : [])
      .filter(isRecord)
      .map((chain, index) => {
        const field = `crypto_playbook.chains[${index}]`;

        return {
          entity: requireString(chain.entity, `${field}.entity`),
          kind: requireString(chain.kind, `${field}.kind`),
          measures: requireString(chain.measures, `${field}.measures`),
          mappingSettled: chain.mapping_settled === true,
          links: (Array.isArray(chain.links) ? chain.links : [])
            .filter(isRecord)
            .map((link, linkIndex) => {
              const row = `${field}.links[${linkIndex}]`;

              return {
                stage: requireString(link.stage, `${row}.stage`),
                label: requireString(link.label, `${row}.label`),
                stated: optionalString(link.stated, `${row}.stated`),
                window: optionalString(link.window, `${row}.window`),
                standing: requireString(link.standing, `${row}.standing`),
                standingStated: requireString(
                  link.standing_stated,
                  `${row}.standing_stated`,
                ),
                availabilityStated: requireString(
                  link.availability_stated,
                  `${row}.availability_stated`,
                ),
                methodology: optionalString(
                  link.methodology,
                  `${row}.methodology`,
                ),
                because: optionalString(link.because, `${row}.because`),
              };
            }),
          mechanism: requireString(chain.mechanism, `${field}.mechanism`),
          mechanismStated: requireString(
            chain.mechanism_stated,
            `${field}.mechanism_stated`,
          ),
          mechanismSourceWording: optionalString(
            chain.mechanism_source_wording,
            `${field}.mechanism_source_wording`,
          ),
          because: requireString(chain.because, `${field}.because`),
        };
      }),
    unmappedBecause: optionalString(
      value.unmapped_because,
      "crypto_playbook.unmapped_because",
    ),
  };
}


function parseMarketObservations(
  value: unknown,
  field: string,
): readonly MarketObservationView[] {
  return (Array.isArray(value) ? value : [])
    .filter(isRecord)
    .map((row, index) => {
      const at = `${field}[${index}]`;

      return {
        metric: requireString(row.metric, `${at}.metric`),
        label: requireString(row.label, `${at}.label`),
        interval: requireString(row.interval, `${at}.interval`),
        intervalStated: requireString(row.interval_stated, `${at}.interval_stated`),
        stated: optionalString(row.stated, `${at}.stated`),
        standing: requireString(row.standing, `${at}.standing`),
        standingStated: requireString(row.standing_stated, `${at}.standing_stated`),
        derived: row.derived === true,
        universe: optionalString(row.universe, `${at}.universe`),
        source: optionalString(row.source, `${at}.source`),
        age: optionalString(row.age, `${at}.age`),
        because: optionalString(row.because, `${at}.because`),
      };
    });
}

function parseCryptoMarket(value: unknown): DossierCryptoMarket | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "crypto_market".');
  }

  const peer = isRecord(value.peer) ? value.peer : null;

  return {
    market: parseMarketObservations(value.market, "crypto_market.market"),
    marketSource: optionalString(value.market_source, "crypto_market.market_source"),
    marketAge: optionalString(value.market_age, "crypto_market.market_age"),
    returns: parseMarketObservations(value.returns, "crypto_market.returns"),
    peer:
      peer === null
        ? null
        : {
            key: requireString(peer.key, "crypto_market.peer.key"),
            name: requireString(peer.name, "crypto_market.peer.name"),
            provider: requireString(peer.provider, "crypto_market.peer.provider"),
            selectedBecause: requireString(
              peer.selected_because,
              "crypto_market.peer.selected_because",
            ),
            caveats: (Array.isArray(peer.caveats) ? peer.caveats : []).filter(
              (item): item is string => typeof item === "string",
            ),
          },
    peerUnavailableBecause: optionalString(
      value.peer_unavailable_because,
      "crypto_market.peer_unavailable_because",
    ),
    considered: (Array.isArray(value.considered) ? value.considered : [])
      .filter(isRecord)
      .map((row, index) => ({
        name: requireString(row.name, `crypto_market.considered[${index}].name`),
        rejectedBecause: requireString(
          row.rejected_because,
          `crypto_market.considered[${index}].rejected_because`,
        ),
      })),
    peerObservations: parseMarketObservations(
      value.peer_observations,
      "crypto_market.peer_observations",
    ),
    relative: (Array.isArray(value.relative) ? value.relative : [])
      .filter(isRecord)
      .map((row, index) => {
        const at = `crypto_market.relative[${index}]`;

        return {
          interval: requireString(row.interval, `${at}.interval`),
          comparator: requireString(row.comparator, `${at}.comparator`),
          subjectReturn: requireString(row.subject_return, `${at}.subject_return`),
          comparatorReturn: requireString(
            row.comparator_return,
            `${at}.comparator_return`,
          ),
          delta: requireString(row.delta, `${at}.delta`),
          standing: requireString(row.standing, `${at}.standing`),
          stated: requireString(row.stated, `${at}.stated`),
          caveat: optionalString(row.caveat, `${at}.caveat`),
        };
      }),
    concentrations: (Array.isArray(value.concentrations) ? value.concentrations : [])
      .filter(isRecord)
      .map((row, index) => ({
        comparator: requireString(
          row.comparator,
          `crypto_market.concentrations[${index}].comparator`,
        ),
        stated: requireString(
          row.stated,
          `crypto_market.concentrations[${index}].stated`,
        ),
      })),
    uncompared: (Array.isArray(value.uncompared) ? value.uncompared : []).filter(
      (item): item is string => typeof item === "string",
    ),
    unavailableBecause: optionalString(
      value.unavailable_because,
      "crypto_market.unavailable_because",
    ),
  };
}


function parseSupply(value: unknown): DossierSupply | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error('Expected an object or null at "supply".');
  }

  const strings = (raw: unknown): readonly string[] =>
    (Array.isArray(raw) ? raw : []).filter(
      (item): item is string => typeof item === "string",
    );

  return {
    figures: (Array.isArray(value.figures) ? value.figures : [])
      .filter(isRecord)
      .map((row, index) => {
        const at = `supply.figures[${index}]`;

        return {
          concept: requireString(row.concept, `${at}.concept`),
          conceptStated: requireString(row.concept_stated, `${at}.concept_stated`),
          stated: requireString(row.stated, `${at}.stated`),
          definedBy: requireString(row.defined_by, `${at}.defined_by`),
          methodology: requireString(row.methodology, `${at}.methodology`),
          disclosed: row.disclosed === true,
          excludes: strings(row.excludes),
          source: requireString(row.source, `${at}.source`),
          age: optionalString(row.age, `${at}.age`),
          reportedAs: optionalString(row.reported_as, `${at}.reported_as`),
          standing: requireString(row.standing, `${at}.standing`),
          standingStated: requireString(row.standing_stated, `${at}.standing_stated`),
          authority: requireString(row.authority, `${at}.authority`),
          authorityStated: requireString(
            row.authority_stated,
            `${at}.authority_stated`,
          ),
          because: optionalString(row.because, `${at}.because`),
          caveats: strings(row.caveats),
        };
      }),
    comparisons: (Array.isArray(value.comparisons) ? value.comparisons : [])
      .filter(isRecord)
      .map((row, index) => {
        const at = `supply.comparisons[${index}]`;

        return {
          verdict: requireString(row.verdict, `${at}.verdict`),
          verdictStated: requireString(row.verdict_stated, `${at}.verdict_stated`),
          leftSource: requireString(row.left_source, `${at}.left_source`),
          leftStated: requireString(row.left_stated, `${at}.left_stated`),
          rightSource: requireString(row.right_source, `${at}.right_source`),
          rightStated: requireString(row.right_stated, `${at}.right_stated`),
          because: requireString(row.because, `${at}.because`),
        };
      }),
    methodologyDisagreement: value.methodology_disagreement === true,
    unresolved: strings(value.unresolved),
    unavailableBecause: optionalString(
      value.unavailable_because,
      "supply.unavailable_because",
    ),
  };
}

function parseCommittees(
  value: unknown,
): readonly DossierCommitteeOpinion[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord).map((opinion, index) => ({
    committee: requireString(opinion.committee, `committees[${index}].committee`),
    stance: optionalString(opinion.stance, `committees[${index}].stance`),
    abstained: opinion.abstained === true,
    abstainedBecause: optionalString(
      opinion.abstained_because,
      `committees[${index}].abstained_because`,
    ),
    confidence: optionalString(
      opinion.confidence,
      `committees[${index}].confidence`,
    ),
    decidedBy: requireString(
      opinion.decided_by,
      `committees[${index}].decided_by`,
    ),
    summary: requireString(opinion.summary, `committees[${index}].summary`),
    supporting: parseStatements(
      opinion.supporting,
      `committees[${index}].supporting`,
    ),
    opposing: parseStatements(
      opinion.opposing,
      `committees[${index}].opposing`,
    ),
    uncertainty: Array.isArray(opinion.uncertainty)
      ? opinion.uncertainty.filter(isRecord).map((item, itemIndex) => ({
          kind: requireString(
            item.kind,
            `committees[${index}].uncertainty[${itemIndex}].kind`,
          ),
          about: requireString(
            item.about,
            `committees[${index}].uncertainty[${itemIndex}].about`,
          ),
          resolvable: item.resolvable === true,
        }))
      : [],
  }));
}

function parseStatements(value: unknown, field: string): string[] {
  const items = Array.isArray(value) ? value : [];

  return items.map((item, index) => requireString(item, `${field}[${index}]`));
}

function parseAgreement(
  value: unknown,
  field: string,
): DossierAgreement | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error(`${field} is not a JSON object.`);
  }

  return {
    agreeing: requireNumber(value.agreeing, `${field}.agreeing`),
    readings: requireNumber(value.readings, `${field}.readings`),
    settled: requireBoolean(value.settled, `${field}.settled`),
  };
}

function parseBusinessUnderstanding(
  value: unknown,
): DossierBusinessUnderstanding | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error("understanding.business is not a JSON object.");
  }

  const segments = Array.isArray(value.segments) ? value.segments : [];
  const mechanisms = Array.isArray(value.mechanisms) ? value.mechanisms : [];
  const missing = Array.isArray(value.not_established)
    ? value.not_established
    : [];

  return {
    source: requireString(value.source, "understanding.business.source"),
    read: requireString(value.read, "understanding.business.read"),
    quorate: requireBoolean(value.quorate, "understanding.business.quorate"),
    observationCount: requireNumber(
      value.observation_count,
      "understanding.business.observation_count",
    ),
    quorum: requireNumber(value.quorum, "understanding.business.quorum"),
    engine: requireString(value.engine, "understanding.business.engine"),
    archetype: optionalString(value.archetype, "understanding.business.archetype"),
    undecidedBecause: optionalString(
      value.undecided_because,
      "understanding.business.undecided_because",
    ),
    narrowest: parseAgreement(
      value.narrowest,
      "understanding.business.narrowest",
    ),
    segments: segments.map((segment, index) => {
      if (!isRecord(segment)) {
        throw new Error(`understanding.business.segments[${index}] is not an object.`);
      }

      return {
        name: requireString(
          segment.name,
          `understanding.business.segments[${index}].name`,
        ),
        share: optionalNumber(segment.share),
        unmeasuredBecause: optionalString(
          segment.unmeasured_because,
          `understanding.business.segments[${index}].unmeasured_because`,
        ),
        earns: stringList(segment.earns),
        earnsBecause: optionalString(
          segment.earns_because,
          `understanding.business.segments[${index}].earns_because`,
        ),
        depends: optionalString(
          segment.depends,
          `understanding.business.segments[${index}].depends`,
        ),
        dependsQuoted: optionalString(
          segment.depends_quoted,
          `understanding.business.segments[${index}].depends_quoted`,
        ),
        dependsSupport: optionalString(
          segment.depends_support,
          `understanding.business.segments[${index}].depends_support`,
        ),
      };
    }),
    segmentsBecause: optionalString(
      value.segments_because,
      "understanding.business.segments_because",
    ),
    mechanisms: mechanisms.map((mechanism, index) => {
      if (!isRecord(mechanism)) {
        throw new Error(
          `understanding.business.mechanisms[${index}] is not an object.`,
        );
      }

      const support = parseAgreement(
        mechanism.support,
        `understanding.business.mechanisms[${index}].support`,
      );

      if (support === null) {
        throw new Error(
          `understanding.business.mechanisms[${index}].support is missing.`,
        );
      }

      return {
        model: requireString(
          mechanism.model,
          `understanding.business.mechanisms[${index}].model`,
        ),
        through: stringList(mechanism.through),
        coverage: optionalNumber(mechanism.coverage),
        support,
      };
    }),
    notEstablished: missing.map((item, index) => {
      if (!isRecord(item)) {
        throw new Error(
          `understanding.business.not_established[${index}] is not an object.`,
        );
      }

      return {
        segment: requireString(
          item.segment,
          `understanding.business.not_established[${index}].segment`,
        ),
        dimension: requireString(
          item.dimension,
          `understanding.business.not_established[${index}].dimension`,
        ),
        because: requireString(
          item.because,
          `understanding.business.not_established[${index}].because`,
        ),
      };
    }),
  };
}

function parseFinancialUnderstanding(
  value: unknown,
): DossierFinancialUnderstanding | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error("understanding.financial is not a JSON object.");
  }

  const measures = Array.isArray(value.measures) ? value.measures : [];

  return {
    source: requireString(value.source, "understanding.financial.source"),
    read: requireString(value.read, "understanding.financial.read"),
    quorate: requireBoolean(value.quorate, "understanding.financial.quorate"),
    observationCount: requireNumber(
      value.observation_count,
      "understanding.financial.observation_count",
    ),
    quorum: requireNumber(value.quorum, "understanding.financial.quorum"),
    statements: stringList(value.statements),
    language: optionalString(value.language, "understanding.financial.language"),
    languageBecause: optionalString(
      value.language_because,
      "understanding.financial.language_because",
    ),
    measures: measures.map((measure, index) => {
      if (!isRecord(measure)) {
        throw new Error(`understanding.financial.measures[${index}] is not an object.`);
      }

      return {
        measure: requireString(
          measure.measure,
          `understanding.financial.measures[${index}].measure`,
        ),
        label: requireString(
          measure.label,
          `understanding.financial.measures[${index}].label`,
        ),
        value: optionalNumber(measure.value),
        unit: requireString(
          measure.unit,
          `understanding.financial.measures[${index}].unit`,
        ),
        // A measure the platform worded nothing for is a measure with
        // nothing worded, not a corrupt payload. `requireString` refuses
        // an empty string — and reports "expected a string, received
        // string" while doing it — so two empty sentences on AAPL and
        // five on DIS took the whole dossier down to "the backend is
        // unreachable". The page already renders this conditionally.
        stated:
          optionalString(
            measure.stated,
            `understanding.financial.measures[${index}].stated`,
          ) ?? "",
        support: parseAgreement(
          measure.support,
          `understanding.financial.measures[${index}].support`,
        ),
        absentBecause: optionalString(
          measure.absent_because,
          `understanding.financial.measures[${index}].absent_because`,
        ),
      };
    }),
  };
}

function parseUnderstanding(value: unknown): DossierUnderstanding | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error("understanding is not a JSON object.");
  }

  return {
    business: parseBusinessUnderstanding(value.business),
    businessAbsentBecause: optionalString(
      value.business_absent_because,
      "understanding.business_absent_because",
    ),
    financial: parseFinancialUnderstanding(value.financial),
    financialAbsentBecause: optionalString(
      value.financial_absent_because,
      "understanding.financial_absent_because",
    ),
  };
}

function parseSynthesisFacts(
  value: unknown,
  field: string,
): DossierSynthesisFact[] {
  const items = Array.isArray(value) ? value : [];

  return items.map((item, index) => {
    if (!isRecord(item)) {
      throw new Error(`${field}[${index}] is not an object.`);
    }

    return {
      statement: requireString(item.statement, `${field}[${index}].statement`),
      origin: requireString(item.origin, `${field}[${index}].origin`),
      committee: optionalString(item.committee, `${field}[${index}].committee`),
    };
  });
}

function parseSynthesis(value: unknown): DossierSynthesis | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error("synthesis is not a JSON object.");
  }

  const conditions = Array.isArray(value.review_if) ? value.review_if : [];

  return {
    state: requireString(value.state, "synthesis.state"),
    conviction: optionalNumber(value.conviction),
    because: parseSynthesisFacts(value.because, "synthesis.because"),
    becauseAbsent: optionalString(
      value.because_absent,
      "synthesis.because_absent",
    ),
    despite: parseSynthesisFacts(value.despite, "synthesis.despite"),
    despiteAbsent: optionalString(
      value.despite_absent,
      "synthesis.despite_absent",
    ),
    reviewIf: conditions.map((item, index) => {
      if (!isRecord(item)) {
        throw new Error(`synthesis.review_if[${index}] is not an object.`);
      }

      return {
        condition: requireString(
          item.condition,
          `synthesis.review_if[${index}].condition`,
        ),
        origin: requireString(
          item.origin,
          `synthesis.review_if[${index}].origin`,
        ),
        wouldChange: optionalString(
          item.would_change,
          `synthesis.review_if[${index}].would_change`,
        ),
      };
    }),
    reviewIfAbsent: optionalString(
      value.review_if_absent,
      "synthesis.review_if_absent",
    ),
    uncertainty: (Array.isArray(value.uncertainty) ? value.uncertainty : [])
      .filter(isRecord)
      .map((item, index) => ({
        committee: requireString(
          item.committee,
          `synthesis.uncertainty[${index}].committee`,
        ),
        kind: requireString(item.kind, `synthesis.uncertainty[${index}].kind`),
        about: requireString(
          item.about,
          `synthesis.uncertainty[${index}].about`,
        ),
        resolvable: item.resolvable === true,
      })),
    uncertaintyAbsent: optionalString(
      value.uncertainty_absent,
      "synthesis.uncertainty_absent",
    ),
    deliberation: isRecord(value.deliberation)
      ? {
          agreement: requireString(
            value.deliberation.agreement,
            "synthesis.deliberation.agreement",
          ),
          prevailed: requireString(
            value.deliberation.prevailed,
            "synthesis.deliberation.prevailed",
          ),
          over: optionalString(
            value.deliberation.over,
            "synthesis.deliberation.over",
          ),
          because: requireString(
            value.deliberation.because,
            "synthesis.deliberation.because",
          ),
        }
      : null,
    established: parseSynthesisFacts(
      value.established,
      "synthesis.established",
    ),
    challengeable: requireBoolean(
      value.challengeable,
      "synthesis.challengeable",
    ),
    deliberated: value.deliberated === true,
  };
}

function parseNarrative(value: unknown): DossierNarrative | null {
  if (value === null || value === undefined) {
    return null;
  }

  if (!isRecord(value)) {
    throw new Error("narrative is not a JSON object.");
  }

  const sections = Array.isArray(value.sections) ? value.sections : [];
  const findings = Array.isArray(value.findings) ? value.findings : [];

  return {
    headline: requireString(value.headline, "narrative.headline"),
    recommendation: requireString(
      value.recommendation,
      "narrative.recommendation",
    ),
    sections: sections.map((section, index) => {
      if (!isRecord(section)) {
        throw new Error(`narrative.sections[${index}] is not an object.`);
      }

      return {
        section: requireString(
          section.section,
          `narrative.sections[${index}].section`,
        ),
        text: requireString(section.text, `narrative.sections[${index}].text`),
        findingIds: stringList(section.finding_ids),
      };
    }),
    findings: findings.map((finding, index) => {
      if (!isRecord(finding)) {
        throw new Error(`narrative.findings[${index}] is not an object.`);
      }

      return {
        id: requireString(finding.id, `narrative.findings[${index}].id`),
        statement: requireString(
          finding.statement,
          `narrative.findings[${index}].statement`,
        ),
        source: requireString(
          finding.source,
          `narrative.findings[${index}].source`,
        ),
      };
    }),
    model: requireString(value.model, "narrative.model"),
    written: requireString(value.written, "narrative.written"),
  };
}

function parseDossier(payload: unknown): DossierViewModel {
  if (!isRecord(payload)) {
    throw new Error("The dossier response is not a JSON object.");
  }

  const scores = payload.scores;

  if (!isRecord(scores)) {
    throw new Error("The dossier response has no scores object.");
  }

  return {
    symbol: requireString(payload.symbol, "symbol"),
    definition: parseDefinition(payload.definition),
    decisionState: requireString(payload.decision_state, "decision_state"),
    conviction: optionalNumber(payload.conviction),
    convictionLabel: optionalString(
      payload.conviction_label,
      "conviction_label",
    ),
    committeeAgreement: optionalNumber(payload.committee_agreement),
    rationale: requireString(payload.rationale, "rationale"),
    trend: isRecord(payload.trend)
      ? {
          direction: requireString(payload.trend.direction, "trend.direction"),
          stated: requireString(payload.trend.stated, "trend.stated"),
        }
      : null,
    playbook: isRecord(payload.playbook)
      ? {
          kind: requireString(payload.playbook.kind, "playbook.kind"),
          name: requireString(payload.playbook.name, "playbook.name"),
          explanation: requireString(
            payload.playbook.explanation,
            "playbook.explanation",
          ),
          priorities: stringList(payload.playbook.priorities),
          coverage: (Array.isArray(payload.playbook.coverage)
            ? payload.playbook.coverage
            : []
          )
            .filter(isRecord)
            .map((item, index) => ({
              analyst: requireString(
                item.analyst,
                `playbook.coverage[${index}].analyst`,
              ),
              label: requireString(
                item.label,
                `playbook.coverage[${index}].label`,
              ),
              covered: item.covered === true,
              reason: optionalString(
                item.reason,
                `playbook.coverage[${index}].reason`,
              ),
            })),
          classified: payload.playbook.classified === true,
        }
      : null,
    classification: parseClassification(payload.classification),
    decisionCourse: parseDecisionCourse(payload.decision_course),
    convictionChange: isRecord(payload.conviction_change)
      ? {
          previous: requireNumber(
            payload.conviction_change.previous,
            "conviction_change.previous",
          ),
          delta: requireNumber(
            payload.conviction_change.delta,
            "conviction_change.delta",
          ),
          stated: requireString(
            payload.conviction_change.stated,
            "conviction_change.stated",
          ),
          because: stringList(payload.conviction_change.because),
          unexplained: payload.conviction_change.unexplained === true,
        }
      : null,
    action: isRecord(payload.action)
      ? {
          kind: requireString(payload.action.kind, "action.kind"),
          statement: requireString(payload.action.statement, "action.statement"),
          because: requireString(payload.action.because, "action.because"),
          checkpoint: optionalString(payload.action.checkpoint, "action.checkpoint"),
        }
      : null,
    summary: requireString(payload.summary, "summary"),
    expectedHoldingPeriod: requireString(
      payload.expected_holding_period,
      "expected_holding_period",
    ),
    catalysts: stringList(payload.catalysts),
    invalidationConditions: stringList(payload.invalidation_conditions),
    nextTrigger: optionalString(payload.next_trigger, "next_trigger"),
    securityEvidenced: requireBoolean(
      payload.security_evidenced,
      "security_evidenced",
    ),
    evidenceWeighed: stringList(payload.evidence_weighed),
    strengths: stringList(payload.strengths),
    risks: stringList(payload.risks),
    missingEvidence: stringList(payload.missing_evidence),
    scores: {
      quality: parseScore(scores.quality, "scores.quality"),
      evidence: parseScore(scores.evidence, "scores.evidence"),
      valuation: parseScore(scores.valuation, "scores.valuation"),
      safety: parseScore(scores.safety, "scores.safety"),
      portfolioFit: parseScore(scores.portfolio_fit, "scores.portfolio_fit"),
    },
    contextStrengths: stringList(payload.context_strengths),
    contextRisks: stringList(payload.context_risks),
    committees: parseCommittees(payload.committees),
    evidenceAsOf: parseProvenance(payload.evidence_as_of, "evidence_as_of"),
    tokenRating: parseTokenRating(payload.token_rating),
    fundCost: parseFundCost(payload.fund_cost),
    assetProfile: parseAssetProfile(payload.asset_profile),
    protocolFundamentals: parseProtocolFundamentals(
      payload.protocol_fundamentals,
    ),
    cryptoPlaybook: parseCryptoPlaybook(payload.crypto_playbook),
    cryptoMarket: parseCryptoMarket(payload.crypto_market),
    supply: parseSupply(payload.supply),
    narrative: parseNarrative(payload.narrative),
    narrativeAbsent: optionalString(
      payload.narrative_absent,
      "narrative_absent",
    ),
    understanding: parseUnderstanding(payload.understanding),
    synthesis: parseSynthesis(payload.synthesis),
  };
}

export async function getDossier(symbol: string): Promise<DossierResult> {
  const endpoint = `${BACKEND_URL}/executive/${encodeURIComponent(
    symbol,
  )}/dossier`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      const responseBody = await response.text();

      throw new Error(
        `Backend returned ${response.status} for ${endpoint}: ${responseBody.slice(0, 300)}`,
      );
    }

    return {
      dossier: parseDossier(await response.json()),
      source: "backend",
      backendUrl: endpoint,
    };
  } catch (error) {
    // An unreachable backend means nothing is known about this case.
    // Nothing is what is shown.
    return {
      dossier: null,
      source: "unavailable",
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
