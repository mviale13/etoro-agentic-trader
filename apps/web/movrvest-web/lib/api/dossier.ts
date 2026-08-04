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

/** Null means the platform did not measure it — never zero. */
export interface DossierScores {
  quality: number | null;
  evidence: number;
  valuation: number | null;
  risk: number | null;
  portfolioFit: number | null;
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
  previousDecisions: string | null;

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
    previousDecisions: optionalString(
      payload.previous_decisions,
      "previous_decisions",
    ),
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
      quality: optionalNumber(scores.quality),
      evidence: requireNumber(scores.evidence, "scores.evidence"),
      valuation: optionalNumber(scores.valuation),
      risk: optionalNumber(scores.risk),
      portfolioFit: optionalNumber(scores.portfolio_fit),
    },
    contextStrengths: stringList(payload.context_strengths),
    contextRisks: stringList(payload.context_risks),
    committees: parseCommittees(payload.committees),
    evidenceAsOf: parseProvenance(payload.evidence_as_of, "evidence_as_of"),
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
