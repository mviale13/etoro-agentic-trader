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

export interface DossierCommitteeEvidence {
  statement: string;
  source: string;
}

export interface DossierCommitteeOpinion {
  committee: string;
  recommendation: string;
  /** How sure the committee is of its own view. Null when it abstained. */
  confidence: number | null;
  /** An abstention is not opposition, and is never rendered as one. */
  abstained: boolean;
  summary: string;
  evidence: readonly DossierCommitteeEvidence[];
}

/**
 * One score, and the backend's own account of why it is that number.
 *
 * `value` null means the platform did not measure it — never zero, and
 * `basis` then says which measurement was missing. The basis is written
 * where the score is computed; nothing on this side composes it.
 */
export interface DossierScore {
  value: number | null;
  basis: string;
  evidence: readonly string[];
  /** "measurement" | "policy" | "assessment" — the backend's own word. */
  kind: string;
  /** The same, worded for a reader. Never composed on this side. */
  kindStated: string;
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
export interface DossierPlaybook {
  kind: string;
  name: string;
  explanation: string;
  priorities: readonly string[];
  coverage: readonly PlaybookCoverage[];
  /** False when no industry was reported, so nothing was chosen on evidence. */
  classified: boolean;
}

export interface DossierViewModel {
  symbol: string;

  decisionState: string;
  conviction: number;
  convictionLabel: string;
  /** Null where no committee could form a view — not disagreement. */
  committeeAgreement: number | null;
  rationale: string;
  /** Null when the CIO has no recorded history for this symbol. */
  trend: DecisionTrendViewModel | null;
  action: ExecutiveActionViewModel | null;
  convictionChange: ConvictionChangeViewModel | null;
  playbook: DossierPlaybook | null;

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
  conviction: number;
  because: readonly DossierSynthesisFact[];
  becauseAbsent: string | null;
  despite: readonly DossierSynthesisFact[];
  despiteAbsent: string | null;
  reviewIf: readonly DossierReviewCondition[];
  reviewIfAbsent: string | null;
  /** What the filing establishes — carried, and not consumed by the decision. */
  established: readonly DossierSynthesisFact[];
  /** Whether the investor is given anything to disagree with. */
  challengeable: boolean;
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
    basis: requireString(value.basis, `${field}.basis`),
    evidence: stringList(value.evidence),
    kind: requireString(value.kind, `${field}.kind`),
    kindStated: requireString(value.kind_stated, `${field}.kind_stated`),
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

function parseCommittees(
  value: unknown,
): readonly DossierCommitteeOpinion[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord).map((opinion, index) => ({
    committee: requireString(opinion.committee, `committees[${index}].committee`),
    recommendation: requireString(
      opinion.recommendation,
      `committees[${index}].recommendation`,
    ),
    confidence: optionalNumber(opinion.confidence),
    abstained: opinion.abstained === true,
    summary: requireString(opinion.summary, `committees[${index}].summary`),
    evidence: Array.isArray(opinion.evidence)
      ? opinion.evidence.filter(isRecord).map((item, itemIndex) => ({
          statement: requireString(
            item.statement,
            `committees[${index}].evidence[${itemIndex}].statement`,
          ),
          source: requireString(
            item.source,
            `committees[${index}].evidence[${itemIndex}].source`,
          ),
        }))
      : [],
  }));
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
        stated: requireString(
          measure.stated,
          `understanding.financial.measures[${index}].stated`,
        ),
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
    conviction: requireNumber(value.conviction, "synthesis.conviction"),
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
    established: parseSynthesisFacts(
      value.established,
      "synthesis.established",
    ),
    challengeable: requireBoolean(
      value.challengeable,
      "synthesis.challengeable",
    ),
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
    decisionState: requireString(payload.decision_state, "decision_state"),
    conviction: requireNumber(payload.conviction, "conviction"),
    convictionLabel: requireString(
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
