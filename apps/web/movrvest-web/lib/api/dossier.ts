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
