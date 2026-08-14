/**
 * Client for GET /crypto/{symbol}/dossier.
 *
 * A strict mirror of the backend's payload and nothing more. **This file
 * is the enforcement point for the slice's one hard rule: the frontend
 * calculates nothing analytical.** There is no threshold here, no band,
 * no applicability rule, no interpretation, no verdict and no derived
 * economic claim — every sentence an investor reads arrives already
 * worded, and this side chooses only where to put it.
 *
 * Two consequences worth stating, because both were tempting:
 *
 * - **No fallback prose.** Where the backend says an interpretation is
 *   not established, this side renders that sentence. It does not
 *   substitute a friendlier one, and it does not describe a measurement
 *   in economic terms the backend declined to use. That is the frontend
 *   half of Zero Fake Meaning.
 * - **A malformed payload fails loudly.** A dossier that quietly
 *   substituted a default would be the failure that once served two
 *   200-OK dossiers reading "the backend is unreachable". A required
 *   field missing is an error; an *absent* one is a null the backend
 *   sent on purpose, and those are different things.
 */

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireRecord(value: unknown, field: string): UnknownRecord {
  if (!isRecord(value)) {
    throw new Error(`Expected an object at "${field}".`);
  }

  return value;
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(
      `Expected a string at "${field}", received ${typeof value}`,
    );
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
    throw new Error(
      `Expected a number at "${field}", received ${typeof value}`,
    );
  }

  return value;
}

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

function recordList(value: unknown, field: string): readonly UnknownRecord[] {
  if (!Array.isArray(value)) {
    throw new Error(`Expected an array at "${field}".`);
  }

  return value.map((item, index) => requireRecord(item, `${field}[${index}]`));
}

/** A section the backend chose not to send. Absent, never empty. */
function optionalSection<T>(
  value: unknown,
  field: string,
  parse: (record: UnknownRecord) => T,
): T | null {
  if (value === null || value === undefined) {
    return null;
  }

  return parse(requireRecord(value, field));
}

// ── identity ────────────────────────────────────────────────────────

/** One analytical lens, and what it reads. */
export interface CapabilityView {
  key: string;
  label: string;
  reads: string;
}

/** An archetype weighed and not chosen, with the reason it was not. */
export interface ConsideredArchetypeView {
  archetype: string;
  notChosenBecause: string;
}

/** One evidence demand behind a question, met or not. */
export interface QuestionEvidenceView {
  demand: string;
  met: boolean;
  stated: string | null;
  standingStated: string;
  source: string | null;
  age: string | null;
  because: string | null;
}

/**
 * One investment question, and whether it is even asked of this asset.
 *
 * `applicability` is settled from the archetype before any figure is
 * read. This side renders that decision and can never participate in
 * it — which is why the reason arrives as a sentence rather than as a
 * code this page would have to translate.
 */
export interface CryptoQuestionView {
  key: string;
  label: string;
  asks: string;
  mattersBecause: string;
  cell: string;
  cellStated: string;
  applicability: string;
  applicabilityBecause: string;
  askedBy: string | null;
  bestStandingStated: string;
  evidence: readonly QuestionEvidenceView[];
}

export interface CryptoIdentity {
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
  capabilities: readonly CapabilityView[];
  /** Questions this kind of asset needs that the platform has not built. */
  unmodelled: readonly string[];
  questions: readonly CryptoQuestionView[];
}

function parseQuestion(
  record: UnknownRecord,
  field: string,
): CryptoQuestionView {
  return {
    key: requireString(record.key, `${field}.key`),
    label: requireString(record.label, `${field}.label`),
    asks: requireString(record.asks, `${field}.asks`),
    mattersBecause: requireString(
      record.matters_because,
      `${field}.matters_because`,
    ),
    cell: requireString(record.cell, `${field}.cell`),
    cellStated: requireString(record.cell_stated, `${field}.cell_stated`),
    applicability: requireString(
      record.applicability,
      `${field}.applicability`,
    ),
    applicabilityBecause: requireString(
      record.applicability_because,
      `${field}.applicability_because`,
    ),
    askedBy: optionalString(record.asked_by, `${field}.asked_by`),
    bestStandingStated: requireString(
      record.best_standing_stated,
      `${field}.best_standing_stated`,
    ),
    evidence: recordList(record.evidence, `${field}.evidence`).map(
      (item, index) => ({
        demand: requireString(
          item.demand,
          `${field}.evidence[${index}].demand`,
        ),
        met: requireBoolean(item.met, `${field}.evidence[${index}].met`),
        stated: optionalString(
          item.stated,
          `${field}.evidence[${index}].stated`,
        ),
        standingStated: requireString(
          item.standing_stated,
          `${field}.evidence[${index}].standing_stated`,
        ),
        source: optionalString(
          item.source,
          `${field}.evidence[${index}].source`,
        ),
        age: optionalString(item.age, `${field}.evidence[${index}].age`),
        because: optionalString(
          item.because,
          `${field}.evidence[${index}].because`,
        ),
      }),
    ),
  };
}

function parseIdentity(record: UnknownRecord): CryptoIdentity {
  return {
    archetype: requireString(record.archetype, "playbook.archetype"),
    name: requireString(record.name, "playbook.name"),
    explanation: requireString(record.explanation, "playbook.explanation"),
    confidence: requireString(record.confidence, "playbook.confidence"),
    confidenceStated: requireString(
      record.confidence_stated,
      "playbook.confidence_stated",
    ),
    because: requireString(record.because, "playbook.because"),
    restsOn: stringList(record.rests_on),
    doesNotEstablish: stringList(record.does_not_establish),
    alternatives: recordList(record.alternatives, "playbook.alternatives").map(
      (item, index) => ({
        archetype: requireString(
          item.archetype,
          `playbook.alternatives[${index}].archetype`,
        ),
        notChosenBecause: requireString(
          item.not_chosen_because,
          `playbook.alternatives[${index}].not_chosen_because`,
        ),
      }),
    ),
    notClassifiedFrom: stringList(record.not_classified_from),
    capabilities: recordList(record.capabilities, "playbook.capabilities").map(
      (item, index) => ({
        key: requireString(item.key, `playbook.capabilities[${index}].key`),
        label: requireString(
          item.label,
          `playbook.capabilities[${index}].label`,
        ),
        reads: requireString(
          item.reads,
          `playbook.capabilities[${index}].reads`,
        ),
      }),
    ),
    unmodelled: stringList(record.unmodelled),
    questions: recordList(record.questions, "playbook.questions").map(
      (item, index) => parseQuestion(item, `playbook.questions[${index}]`),
    ),
  };
}

/** One economic entity mapped to this security, and what it measures. */
export interface ProtocolEntityView {
  key: string;
  name: string;
  kind: string;
  measures: string;
  mappingBasis: string;
  mappingSettled: boolean;
}

export interface ProtocolView {
  entities: readonly ProtocolEntityView[];
  unmappedBecause: string | null;
}

// ── investor assessment (#117 / #119) ───────────────────────────────

/**
 * Why a measurement matters, and the contract that established it.
 *
 * Rendered exactly as three given strings. **This side never authors a
 * reason and never supplies one when the list is empty** — an empty
 * list means no domain contract licensed an interpretation for this
 * asset, and `interpretationWithheld` carries the refusal in the
 * refusing contract's own words.
 */
export interface LicensedMeaningView {
  question: string;
  stated: string;
  licensedBy: string;
}

export interface ObservedValueView {
  value: number;
  unit: string;
  source: string;
}

export interface InvestorStatementView {
  subject: string;
  /** precise | range | structural | qualified | uncertain | insufficient.
   **Not a ranking** — there is no ordering and none is applied here. */
  shape: string;
  shapeStated: string;
  stated: string;
  qualification: string | null;
  uncertainty: string | null;
  whyItMatters: readonly LicensedMeaningView[];
  interpretationWithheld: string | null;
  observed: readonly ObservedValueView[];
  refs: readonly string[];
}

export interface AssessmentView {
  statements: readonly InvestorStatementView[];
  /** Subjects nothing useful is held about, named rather than omitted. */
  silentAbout: readonly string[];
}

function parseAssessment(record: UnknownRecord): AssessmentView {
  return {
    statements: recordList(record.statements, "assessment.statements").map(
      (item, index) => {
        const field = `assessment.statements[${index}]`;

        return {
          subject: requireString(item.subject, `${field}.subject`),
          shape: requireString(item.shape, `${field}.shape`),
          shapeStated: requireString(
            item.shape_stated,
            `${field}.shape_stated`,
          ),
          stated: requireString(item.stated, `${field}.stated`),
          qualification: optionalString(
            item.qualification,
            `${field}.qualification`,
          ),
          uncertainty: optionalString(item.uncertainty, `${field}.uncertainty`),
          whyItMatters: recordList(
            item.why_it_matters,
            `${field}.why_it_matters`,
          ).map((meaning, position) => ({
            question: requireString(
              meaning.question,
              `${field}.why_it_matters[${position}].question`,
            ),
            stated: requireString(
              meaning.stated,
              `${field}.why_it_matters[${position}].stated`,
            ),
            licensedBy: requireString(
              meaning.licensed_by,
              `${field}.why_it_matters[${position}].licensed_by`,
            ),
          })),
          interpretationWithheld: optionalString(
            item.interpretation_withheld,
            `${field}.interpretation_withheld`,
          ),
          observed: recordList(item.observed, `${field}.observed`).map(
            (value, position) => ({
              value: requireNumber(
                value.value,
                `${field}.observed[${position}].value`,
              ),
              unit: requireString(
                value.unit,
                `${field}.observed[${position}].unit`,
              ),
              source: requireString(
                value.source,
                `${field}.observed[${position}].source`,
              ),
            }),
          ),
          refs: stringList(item.refs),
        };
      },
    ),
    silentAbout: stringList(record.silent_about),
  };
}

// ── asset quality ───────────────────────────────────────────────────

export interface QualityCoverageView {
  applicable: number;
  undetermined: number;
  inScope: number;
  scorable: number;
  answered: number;
  shown: number;
  unanswerable: number;
  outside: number;
}

/**
 * One question's participation. **Never a score row.**
 *
 * `participationStated` is the backend's own sentence for the state, and
 * it is always rendered beside the state so that "not applicable" and
 * "could not be answered" cannot read as two degrees of the same thing.
 */
export interface QualityAnswerView {
  key: string;
  label: string;
  asks: string;
  participation: string;
  participationStated: string;
  stated: string | null;
  because: string | null;
  rule: string | null;
  band: string | null;
  bandMeans: string | null;
  source: string | null;
  shown: readonly string[];
}

export interface QualityView {
  /** HIGH | MEDIUM | LOW | UNKNOWN. **UNKNOWN is not a low score** and
      `because` always says why it is what it is. */
  quality: string;
  because: string;
  coverage: QualityCoverageView;
  answers: readonly QualityAnswerView[];
}

function parseQuality(record: UnknownRecord): QualityView {
  const coverage = requireRecord(record.coverage, "quality.coverage");

  return {
    quality: requireString(record.quality, "quality.quality"),
    because: requireString(record.because, "quality.because"),
    coverage: {
      applicable: requireNumber(coverage.applicable, "quality.applicable"),
      undetermined: requireNumber(
        coverage.undetermined,
        "quality.undetermined",
      ),
      inScope: requireNumber(coverage.in_scope, "quality.in_scope"),
      scorable: requireNumber(coverage.scorable, "quality.scorable"),
      answered: requireNumber(coverage.answered, "quality.answered"),
      shown: requireNumber(coverage.shown, "quality.shown"),
      unanswerable: requireNumber(
        coverage.unanswerable,
        "quality.unanswerable",
      ),
      outside: requireNumber(coverage.outside, "quality.outside"),
    },
    answers: recordList(record.answers, "quality.answers").map(
      (item, index) => {
        const field = `quality.answers[${index}]`;

        return {
          key: requireString(item.key, `${field}.key`),
          label: requireString(item.label, `${field}.label`),
          asks: requireString(item.asks, `${field}.asks`),
          participation: requireString(
            item.participation,
            `${field}.participation`,
          ),
          participationStated: requireString(
            item.participation_stated,
            `${field}.participation_stated`,
          ),
          stated: optionalString(item.stated, `${field}.stated`),
          because: optionalString(item.because, `${field}.because`),
          rule: optionalString(item.rule, `${field}.rule`),
          band: optionalString(item.band, `${field}.band`),
          bandMeans: optionalString(item.band_means, `${field}.band_means`),
          source: optionalString(item.source, `${field}.source`),
          shown: stringList(item.shown),
        };
      },
    ),
  };
}

// ── committees ──────────────────────────────────────────────────────

/**
 * One committee's standing conclusion. **Carried, never compared.**
 *
 * There is no field relating one committee to another because there is
 * no such relation: two committees answering different structural
 * questions are not two votes on one proposition. This side adds no
 * agreement, no tally and no ordering.
 */
export interface CommitteeCellView {
  key: string;
  name: string;
  /** What the committee itself is, in its own words. */
  stated: string;
  question: string | null;
  /** Null for a committee that has recorded no judgment at all. It has
      never run here, so it holds no posture — which is a different fact
      from having run and reached nothing, and the domain keeps the two
      apart as separate types. */
  posture: string | null;
  postureStated: string | null;
  applicability: string | null;
  verdict: string | null;
  verdictStated: string | null;
  because: string | null;
  unavailableBecause: string | null;
  confidenceStated: string | null;
  economicRole: string | null;
  /** Null where no judgment was recorded — never a zero, which would
      say the committee looked and weighed nothing. */
  evidenceCount: number | null;
  refs: readonly string[];
  judgmentsRecorded: number;
  wordingRefused: string | null;
  /** The matrix's own sentence for this cell, whatever its state. It is
      what an unjudged committee has instead of a verdict. */
  cellStated: string;
}

export interface CommitteesView {
  committees: readonly CommitteeCellView[];
}

// ── judged market facts ─────────────────────────────────────────────

/**
 * One figure the validation gate judged, exactly as the backend judged it.
 *
 * Every field is authored server-side: the value's wording, how far it
 * can be trusted, that standing in words, the source, the age, and the
 * sentence explaining the judgment. Nothing here is recomputed,
 * re-ranked or re-worded on this side — a figure whose sources conflict
 * carries no value at all, and the reason it carries none *is* the
 * finding.
 */
export interface FactRowView {
  label: string;
  /** Null where the gate served no value — including every conflict. */
  stated: string | null;
  /** "established" | "claimed" | "calculated" | "conflicted" | "absent". */
  standing: string;
  standingStated: string;
  source: string | null;
  age: string | null;
  /** Why it stands as it does. Always present, and always shown. */
  because: string;
}

export interface FactGroupView {
  title: string;
  rows: readonly FactRowView[];
}

/**
 * What is measured about this asset, and what was refused.
 *
 * `rejected` is the ledger of provider claims the gate would not accept.
 * They are evidence about a source, never candidate values, and this
 * side keeps them structurally apart from the rows above for exactly
 * that reason.
 */
export interface FactsView {
  groups: readonly FactGroupView[];
  rejected: readonly string[];
}

function parseCommittees(record: UnknownRecord): CommitteesView {
  return {
    committees: recordList(record.committees, "committees.committees").map(
      (item, index) => {
        const field = `committees.committees[${index}]`;
        const identity = requireRecord(item.committee, `${field}.committee`);

        return {
          key: requireString(identity.key, `${field}.committee.key`),
          name: requireString(identity.name, `${field}.committee.name`),
          stated: requireString(identity.stated, `${field}.committee.stated`),
          question: optionalString(item.question, `${field}.question`),
          // An unjudged committee sends none of these. It has recorded
          // no judgment, so it has no posture, no applicability reading
          // and no evidence count — and requiring them threw, which
          // took the whole page down with it.
          posture: optionalString(item.posture, `${field}.posture`),
          postureStated: optionalString(
            item.posture_stated,
            `${field}.posture_stated`,
          ),
          applicability: optionalString(
            item.applicability,
            `${field}.applicability`,
          ),
          verdict: optionalString(item.verdict, `${field}.verdict`),
          verdictStated: optionalString(
            item.verdict_stated,
            `${field}.verdict_stated`,
          ),
          because: optionalString(item.because, `${field}.because`),
          unavailableBecause: optionalString(
            item.unavailable_because,
            `${field}.unavailable_because`,
          ),
          confidenceStated: optionalString(
            item.confidence_stated,
            `${field}.confidence_stated`,
          ),
          economicRole: optionalString(
            item.economic_role,
            `${field}.economic_role`,
          ),
          // Null, never zero: a committee that never ran did not weigh
          // nothing, it weighed nothing *yet*.
          evidenceCount:
            item.evidence_count === null || item.evidence_count === undefined
              ? null
              : requireNumber(item.evidence_count, `${field}.evidence_count`),
          refs: stringList(item.refs),
          judgmentsRecorded: requireNumber(
            item.judgments_recorded,
            `${field}.judgments_recorded`,
          ),
          wordingRefused: optionalString(
            item.wording_refused,
            `${field}.wording_refused`,
          ),
          cellStated: requireString(item.stated, `${field}.stated`),
        };
      },
    ),
  };
}

function parseFacts(value: unknown): FactsView | null {
  if (value === null || value === undefined) {
    return null;
  }

  const record = requireRecord(value, "facts");

  return {
    groups: recordList(record.groups, "facts.groups").map((group, index) => {
      const field = `facts.groups[${index}]`;

      return {
        title: requireString(group.title, `${field}.title`),
        rows: recordList(group.rows, `${field}.rows`).map((row, position) => ({
          label: requireString(row.label, `${field}.rows[${position}].label`),
          // Null on purpose wherever the gate served no value — a
          // conflicted figure has none, and inventing one here would be
          // the whole defect this section exists to end.
          stated: optionalString(
            row.stated,
            `${field}.rows[${position}].stated`,
          ),
          standing: requireString(
            row.standing,
            `${field}.rows[${position}].standing`,
          ),
          standingStated: requireString(
            row.standing_stated,
            `${field}.rows[${position}].standing_stated`,
          ),
          source: optionalString(
            row.source,
            `${field}.rows[${position}].source`,
          ),
          age: optionalString(row.age, `${field}.rows[${position}].age`),
          because: requireString(
            row.because,
            `${field}.rows[${position}].because`,
          ),
        })),
      };
    }),
    rejected: recordList(record.rejected, "facts.rejected").map(
      (item, index) =>
        requireString(item.statement, `facts.rejected[${index}].statement`),
    ),
  };
}

// ── supply and issuance ─────────────────────────────────────────────

export interface SupplyFigureView {
  concept: string;
  conceptStated: string;
  stated: string;
  definedBy: string;
  methodology: string;
  disclosed: boolean;
  excludes: readonly string[];
  source: string;
  age: string | null;
  standingStated: string;
  authorityStated: string;
  because: string | null;
  caveats: readonly string[];
}

export interface SupplyComparisonView {
  verdictStated: string;
  leftSource: string;
  leftStated: string;
  rightSource: string;
  rightStated: string;
  because: string;
}

export interface SupplyView {
  figures: readonly SupplyFigureView[];
  comparisons: readonly SupplyComparisonView[];
  methodologyDisagreement: boolean;
  unresolved: readonly string[];
  unavailableBecause: string | null;
}

function parseSupply(record: UnknownRecord): SupplyView {
  return {
    figures: recordList(record.figures, "supply.figures").map((item, index) => {
      const field = `supply.figures[${index}]`;

      return {
        concept: requireString(item.concept, `${field}.concept`),
        conceptStated: requireString(
          item.concept_stated,
          `${field}.concept_stated`,
        ),
        stated: requireString(item.stated, `${field}.stated`),
        definedBy: requireString(item.defined_by, `${field}.defined_by`),
        methodology: requireString(item.methodology, `${field}.methodology`),
        disclosed: requireBoolean(item.disclosed, `${field}.disclosed`),
        excludes: stringList(item.excludes),
        source: requireString(item.source, `${field}.source`),
        age: optionalString(item.age, `${field}.age`),
        standingStated: requireString(
          item.standing_stated,
          `${field}.standing_stated`,
        ),
        authorityStated: requireString(
          item.authority_stated,
          `${field}.authority_stated`,
        ),
        because: optionalString(item.because, `${field}.because`),
        caveats: stringList(item.caveats),
      };
    }),
    comparisons: recordList(record.comparisons, "supply.comparisons").map(
      (item, index) => {
        const field = `supply.comparisons[${index}]`;

        return {
          verdictStated: requireString(
            item.verdict_stated,
            `${field}.verdict_stated`,
          ),
          leftSource: requireString(item.left_source, `${field}.left_source`),
          leftStated: requireString(item.left_stated, `${field}.left_stated`),
          rightSource: requireString(
            item.right_source,
            `${field}.right_source`,
          ),
          rightStated: requireString(
            item.right_stated,
            `${field}.right_stated`,
          ),
          because: requireString(item.because, `${field}.because`),
        };
      },
    ),
    methodologyDisagreement: requireBoolean(
      record.methodology_disagreement,
      "supply.methodology_disagreement",
    ),
    unresolved: stringList(record.unresolved),
    unavailableBecause: optionalString(
      record.unavailable_because,
      "supply.unavailable_because",
    ),
  };
}

export interface IssuanceParameterView {
  name: string;
  value: number;
  unit: string;
  means: string;
  readFrom: string;
}

export interface IssuanceStepView {
  horizon: string;
  issuance: number;
  unit: string;
  ruleVersion: string;
}

/**
 * How new supply enters, and what the rule implies under itself.
 *
 * `path` is the backend's arithmetic under the currently observed
 * policy — **never a forecast** — and `mutabilityStated` is always
 * rendered beside it, because a projection without the sentence saying
 * who could change the rule is a prediction wearing a table.
 */
export interface IssuanceView {
  mechanismStated: string;
  mechanismDescribed: string;
  formula: string;
  mutabilityStated: string;
  mutabilityBecause: string;
  isProjectable: boolean;
  emitted: number | null;
  emittedIsDerived: boolean;
  remaining: number | null;
  currentRate: number | null;
  unit: string;
  position: string;
  parameters: readonly IssuanceParameterView[];
  path: readonly IssuanceStepView[];
  caveats: readonly string[];
}

function parseIssuance(record: UnknownRecord): IssuanceView {
  const state = requireRecord(record.state, "issuance.state");

  return {
    mechanismStated: requireString(
      record.mechanism_stated,
      "issuance.mechanism_stated",
    ),
    mechanismDescribed: requireString(
      record.mechanism_described,
      "issuance.mechanism_described",
    ),
    formula: requireString(record.formula, "issuance.formula"),
    mutabilityStated: requireString(
      record.mutability_stated,
      "issuance.mutability_stated",
    ),
    mutabilityBecause: requireString(
      record.mutability_because,
      "issuance.mutability_because",
    ),
    isProjectable: requireBoolean(
      record.is_projectable,
      "issuance.is_projectable",
    ),
    emitted: optionalNumber(state.emitted),
    emittedIsDerived: requireBoolean(
      state.emitted_is_derived,
      "issuance.state.emitted_is_derived",
    ),
    remaining: optionalNumber(state.remaining),
    currentRate: optionalNumber(state.current_rate),
    unit: requireString(state.unit, "issuance.state.unit"),
    position: requireString(state.position, "issuance.state.position"),
    parameters: recordList(record.parameters, "issuance.parameters").map(
      (item, index) => ({
        name: requireString(item.name, `issuance.parameters[${index}].name`),
        value: requireNumber(item.value, `issuance.parameters[${index}].value`),
        unit: requireString(item.unit, `issuance.parameters[${index}].unit`),
        means: requireString(item.means, `issuance.parameters[${index}].means`),
        readFrom: requireString(
          item.read_from,
          `issuance.parameters[${index}].read_from`,
        ),
      }),
    ),
    path: recordList(record.path, "issuance.path").map((item, index) => ({
      horizon: requireString(item.horizon, `issuance.path[${index}].horizon`),
      issuance: requireNumber(
        item.issuance,
        `issuance.path[${index}].issuance`,
      ),
      unit: requireString(item.unit, `issuance.path[${index}].unit`),
      ruleVersion: requireString(
        item.rule_version,
        `issuance.path[${index}].rule_version`,
      ),
    })),
    caveats: stringList(record.caveats),
  };
}

// ── market ──────────────────────────────────────────────────────────

export interface MarketObservationView {
  label: string;
  intervalStated: string;
  stated: string | null;
  standingStated: string;
  derived: boolean;
  universe: string | null;
  source: string | null;
  because: string | null;
}

export interface RelativeReturnView {
  stated: string;
  comparator: string;
  caveat: string | null;
}

export interface MarketView {
  market: readonly MarketObservationView[];
  returns: readonly MarketObservationView[];
  peerName: string | null;
  peerProvider: string | null;
  peerSelectedBecause: string | null;
  peerCaveats: readonly string[];
  peerUnavailableBecause: string | null;
  relative: readonly RelativeReturnView[];
  uncompared: readonly string[];
  unavailableBecause: string | null;
}

function parseObservation(
  item: UnknownRecord,
  field: string,
): MarketObservationView {
  return {
    label: requireString(item.label, `${field}.label`),
    intervalStated: requireString(
      item.interval_stated,
      `${field}.interval_stated`,
    ),
    stated: optionalString(item.stated, `${field}.stated`),
    standingStated: requireString(
      item.standing_stated,
      `${field}.standing_stated`,
    ),
    derived: requireBoolean(item.derived, `${field}.derived`),
    universe: optionalString(item.universe, `${field}.universe`),
    source: optionalString(item.source, `${field}.source`),
    because: optionalString(item.because, `${field}.because`),
  };
}

function parseMarket(record: UnknownRecord): MarketView {
  const peer = isRecord(record.peer) ? record.peer : null;

  return {
    market: recordList(record.market, "market.market").map((item, index) =>
      parseObservation(item, `market.market[${index}]`),
    ),
    returns: recordList(record.returns, "market.returns").map((item, index) =>
      parseObservation(item, `market.returns[${index}]`),
    ),
    peerName: peer ? requireString(peer.name, "market.peer.name") : null,
    peerProvider: peer
      ? requireString(peer.provider, "market.peer.provider")
      : null,
    peerSelectedBecause: peer
      ? requireString(peer.selected_because, "market.peer.selected_because")
      : null,
    peerCaveats: peer ? stringList(peer.caveats) : [],
    peerUnavailableBecause: optionalString(
      record.peer_unavailable_because,
      "market.peer_unavailable_because",
    ),
    relative: recordList(record.relative, "market.relative").map(
      (item, index) => ({
        stated: requireString(item.stated, `market.relative[${index}].stated`),
        comparator: requireString(
          item.comparator,
          `market.relative[${index}].comparator`,
        ),
        caveat: optionalString(item.caveat, `market.relative[${index}].caveat`),
      }),
    ),
    uncompared: stringList(record.uncompared),
    unavailableBecause: optionalString(
      record.unavailable_because,
      "market.unavailable_because",
    ),
  };
}

// ── what is happening ───────────────────────────────────────────────

export interface IntelligenceClaimView {
  ref: string;
  stated: string;
  /** measured | reported | attributed | inferred — the epistemic type,
      rendered so an opinion never reads as a measurement. */
  claimType: string;
  claimTypeStated: string;
  source: string;
  relevanceStated: string;
  age: string | null;
  doesNotEstablish: string | null;
}

export interface DriverView {
  stated: string;
  directionStated: string;
  supportStated: string;
  mattersBecause: string | null;
  /** Refs into the claims above. A driver cannot be rendered without
      the grounds it names. */
  claims: readonly string[];
}

export interface EventFactView {
  stated: string;
  corroboratedBy: readonly string[];
}

export interface EventInterpretationView {
  stated: string;
  source: string;
  isCausal: boolean;
}

export interface EventView {
  headline: string;
  family: string;
  status: string;
  sources: readonly string[];
  isMultiSource: boolean;
  age: string | null;
  facts: readonly EventFactView[];
  interpretations: readonly EventInterpretationView[];
}

export interface WatchItemView {
  stated: string;
  measuredBy: string;
  because: readonly string[];
}

export interface IntelligenceView {
  thinBecause: string | null;
  claims: readonly IntelligenceClaimView[];
  drivers: readonly DriverView[];
  events: readonly EventView[];
  watchNext: readonly WatchItemView[];
  foundationLines: readonly string[];
  foundationUnresolved: readonly string[];
  relativeContext: readonly string[];
  conflicting: readonly string[];
  surfacesUnread: readonly string[];
}

function parseIntelligence(record: UnknownRecord): IntelligenceView {
  const foundation = requireRecord(
    record.foundation,
    "intelligence.foundation",
  );

  return {
    thinBecause: optionalString(
      record.thin_because,
      "intelligence.thin_because",
    ),
    claims: recordList(record.claims, "intelligence.claims").map(
      (item, index) => {
        const field = `intelligence.claims[${index}]`;

        return {
          ref: requireString(item.ref, `${field}.ref`),
          stated: requireString(item.stated, `${field}.stated`),
          claimType: requireString(item.claim_type, `${field}.claim_type`),
          claimTypeStated: requireString(
            item.claim_type_stated,
            `${field}.claim_type_stated`,
          ),
          source: requireString(item.source, `${field}.source`),
          relevanceStated: requireString(
            item.relevance_stated,
            `${field}.relevance_stated`,
          ),
          age: optionalString(item.age, `${field}.age`),
          doesNotEstablish: optionalString(
            item.does_not_establish,
            `${field}.does_not_establish`,
          ),
        };
      },
    ),
    drivers: recordList(record.drivers, "intelligence.drivers").map(
      (item, index) => {
        const field = `intelligence.drivers[${index}]`;

        return {
          stated: requireString(item.stated, `${field}.stated`),
          directionStated: requireString(
            item.direction_stated,
            `${field}.direction_stated`,
          ),
          supportStated: requireString(
            item.support_stated,
            `${field}.support_stated`,
          ),
          mattersBecause: optionalString(
            item.matters_because,
            `${field}.matters_because`,
          ),
          claims: stringList(item.claims),
        };
      },
    ),
    events: recordList(record.events, "intelligence.events").map(
      (item, index) => {
        const field = `intelligence.events[${index}]`;

        return {
          headline: requireString(item.headline, `${field}.headline`),
          family: requireString(item.family, `${field}.family`),
          status: requireString(item.status, `${field}.status`),
          sources: stringList(item.sources),
          isMultiSource: requireBoolean(
            item.is_multi_source,
            `${field}.is_multi_source`,
          ),
          age: optionalString(item.age, `${field}.age`),
          facts: recordList(item.facts, `${field}.facts`).map(
            (fact, position) => ({
              stated: requireString(
                fact.stated,
                `${field}.facts[${position}].stated`,
              ),
              corroboratedBy: stringList(fact.corroborated_by),
            }),
          ),
          interpretations: recordList(
            item.interpretations,
            `${field}.interpretations`,
          ).map((reading, position) => ({
            stated: requireString(
              reading.stated,
              `${field}.interpretations[${position}].stated`,
            ),
            source: requireString(
              reading.source,
              `${field}.interpretations[${position}].source`,
            ),
            isCausal: requireBoolean(
              reading.is_causal,
              `${field}.interpretations[${position}].is_causal`,
            ),
          })),
        };
      },
    ),
    watchNext: recordList(record.watch_next, "intelligence.watch_next").map(
      (item, index) => ({
        stated: requireString(
          item.stated,
          `intelligence.watch_next[${index}].stated`,
        ),
        measuredBy: requireString(
          item.measured_by,
          `intelligence.watch_next[${index}].measured_by`,
        ),
        because: stringList(item.because),
      }),
    ),
    foundationLines: stringList(foundation.lines),
    foundationUnresolved: stringList(foundation.unresolved),
    relativeContext: stringList(record.relative_context),
    conflicting: stringList(record.conflicting),
    surfacesUnread: stringList(record.surfaces_unread),
  };
}

// ── evidence maturity ───────────────────────────────────────────────

/**
 * How far apart the observations behind a temporal claim are.
 *
 * **Three captures across three weeks are not three weeks of
 * monitoring.** `stated` is the backend's own wording of that, and this
 * side renders it rather than computing a duration from the two dates.
 */
export interface ObservationSpanView {
  count: number;
  stated: string;
  firstAge: string | null;
  lastAge: string | null;
}

export interface TemporalFactView {
  key: string;
  status: string;
  statusStated: string;
  stated: string;
  span: ObservationSpanView;
}

export interface JournalView {
  captures: number;
  facts: readonly TemporalFactView[];
}

function parseJournal(record: UnknownRecord): JournalView {
  return {
    captures: requireNumber(record.captures, "journal.captures"),
    facts: recordList(record.facts, "journal.facts").map((item, index) => {
      const field = `journal.facts[${index}]`;
      const span = requireRecord(item.span, `${field}.span`);

      return {
        key: requireString(item.key, `${field}.key`),
        status: requireString(item.status, `${field}.status`),
        statusStated: requireString(
          item.status_stated,
          `${field}.status_stated`,
        ),
        stated: requireString(item.stated, `${field}.stated`),
        span: {
          count: requireNumber(span.count, `${field}.span.count`),
          stated: requireString(span.stated, `${field}.span.stated`),
          firstAge: optionalString(span.first_age, `${field}.span.first_age`),
          lastAge: optionalString(span.last_age, `${field}.span.last_age`),
        },
      };
    }),
  };
}

// ── the whole dossier ───────────────────────────────────────────────

export interface CryptoDossier {
  symbol: string;
  identity: CryptoIdentity;
  protocol: ProtocolView | null;
  assessment: AssessmentView;
  quality: QualityView | null;
  committees: CommitteesView;
  supply: SupplyView | null;
  issuance: IssuanceView | null;
  market: MarketView | null;
  /** What the validation gate judged about this token's market figures,
      and the provider claims it refused. Served all along, and dropped
      here until this parser learned the key. */
  facts: FactsView | null;
  intelligence: IntelligenceView | null;
  journal: JournalView | null;
}

export interface CryptoDossierResult {
  /** Null when the backend was unreachable or refused. Nothing stands in. */
  dossier: CryptoDossier | null;
  source: "backend" | "unavailable";
  backendUrl: string;
  error?: string;
}

function parseDossier(payload: unknown): CryptoDossier {
  const record = requireRecord(payload, "dossier");

  return {
    symbol: requireString(record.symbol, "symbol"),
    identity: parseIdentity(requireRecord(record.playbook, "playbook")),
    protocol: optionalSection(record.protocol, "protocol", (value) => ({
      entities: recordList(value.entities, "protocol.entities").map(
        (item, index) => {
          const field = `protocol.entities[${index}]`;

          return {
            key: requireString(item.key, `${field}.key`),
            name: requireString(item.name, `${field}.name`),
            kind: requireString(item.kind, `${field}.kind`),
            measures: requireString(item.measures, `${field}.measures`),
            mappingBasis: requireString(
              item.mapping_basis,
              `${field}.mapping_basis`,
            ),
            mappingSettled: requireBoolean(
              item.mapping_settled,
              `${field}.mapping_settled`,
            ),
          };
        },
      ),
      unmappedBecause: optionalString(
        value.unmapped_because,
        "protocol.unmapped_because",
      ),
    })),
    assessment: parseAssessment(requireRecord(record.assessment, "assessment")),
    quality: optionalSection(record.quality, "quality", parseQuality),
    committees: parseCommittees(requireRecord(record.committees, "committees")),
    supply: optionalSection(record.supply, "supply", parseSupply),
    issuance: optionalSection(record.issuance, "issuance", parseIssuance),
    market: optionalSection(record.market, "market", parseMarket),
    facts: parseFacts(record.facts),
    intelligence: optionalSection(
      record.intelligence,
      "intelligence",
      parseIntelligence,
    ),
    journal: optionalSection(record.journal, "journal", parseJournal),
  };
}

export async function getCryptoDossier(
  symbol: string,
): Promise<CryptoDossierResult> {
  const endpoint = `${BACKEND_URL}/crypto/${encodeURIComponent(
    symbol,
  )}/dossier`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      const body = await response.text();

      throw new Error(
        `Backend returned ${response.status} for ${endpoint}: ${body.slice(0, 300)}`,
      );
    }

    return {
      dossier: parseDossier(await response.json()),
      source: "backend",
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      dossier: null,
      source: "unavailable",
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}

export interface CorpusAsset {
  symbol: string;
  name: string;
  established: boolean;
}

/**
 * The assets this platform reads, for the switcher.
 *
 * Served by the backend from the same table that gates the dossier, so
 * a menu entry can never 404 and a newly-read asset needs no frontend
 * change. An unreachable backend yields an empty list rather than a
 * hardcoded one.
 */
export async function getCryptoCorpus(): Promise<readonly CorpusAsset[]> {
  try {
    const response = await fetch(`${BACKEND_URL}/crypto/corpus`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      return [];
    }

    const record = requireRecord(await response.json(), "corpus");

    return recordList(record.assets, "corpus.assets").map((item, index) => ({
      symbol: requireString(item.symbol, `corpus.assets[${index}].symbol`),
      name: requireString(item.name, `corpus.assets[${index}].name`),
      established: requireBoolean(
        item.established,
        `corpus.assets[${index}].established`,
      ),
    }));
  } catch {
    return [];
  }
}
