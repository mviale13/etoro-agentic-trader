/**
 * The latest recorded CIO cycle, read from `GET /cycle/latest`.
 *
 * The homepage used to read its courses from `/executive/portfolio`,
 * which builds a Brain, runs the executive pipeline and appends journal
 * entries — during the page request. Opening the page therefore *made*
 * decisions, and two visits could disagree for reasons that had nothing
 * to do with the account.
 *
 * **This parser fails closed.** It used to coerce: a missing
 * `stream_complete` became `true`, missing numbers became `0`, missing
 * arrays became `[]`, and an unrecognised execution string was cast
 * into the enum. Every one of those turns a broken contract into a
 * plausible fact — a page that quietly reports a complete, quiet,
 * empty review because the payload was malformed. A contract-invalid
 * response now yields **no review at all**, and the caller reports why.
 */

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

/** What happened to the latest recorded attempt. Mirrors the backend enum. */
export const CYCLE_EXECUTIONS = [
  "none_recorded",
  "interrupted",
  "failed",
  "partial",
  "complete",
] as const;

export type CycleExecution = (typeof CYCLE_EXECUTIONS)[number];

/** What the change comparison rested on, or null where none was recorded. */
export const COMPARISON_OUTCOMES = [
  "initial_baseline",
  "compared",
  "refused",
] as const;

export type ComparisonOutcome = (typeof COMPARISON_OUTCOMES)[number];

export interface CycleStage {
  name: string;
  outcome: string;
  because: string;
}

export interface CycleEnvelope {
  kind: string;
  /** The domain's own sentence. Rendered as-is; never recomposed. */
  stated: string;
  policySource: string;
  policyVersion: string;
  evidenceCeiling: string;
  capacityCeilingPct: number | null;
  finalPct: number | null;
  bindingConstraint: string;
  because: string;
  namedGaps: string[];
  qualityAuthority: string | null;
  starterCapped: boolean;
  priceAsOf: string;
  portfolioAsOf: string;
  liquidity: string;
}

export interface CycleCourse {
  symbol: string;
  disposition: string;
  rationale: string;
  conviction: number | null;
  evidenceAsOf: string;
  actionKind: string;
  actionStatement: string;
  actionBecause: string;
  asksForSomething: boolean;
  envelope: CycleEnvelope | null;
}

export interface LastKnownCycle {
  cycleId: string;
  finishedAt: string;
  status: string;
  courses: CycleCourse[];
}

export interface CycleReview {
  execution: CycleExecution;
  cycleId: string | null;
  startedAt: string | null;
  finishedAt: string | null;
  stages: CycleStage[];
  comparisonOutcome: ComparisonOutcome | null;
  comparisonPriorCycleId: string;
  comparisonBecause: string;
  securitiesAsked: number;
  securitiesPriced: number;
  refusals: string[];
  newlyProduced: string[];
  changed: string[];
  unchanged: string[];
  attention: string[];
  courses: CycleCourse[];
  /** Exactly the domain's sentence, or null. Never softened, never defaulted. */
  noActionSuggested: string | null;
  streamComplete: boolean;
  unreadableRecords: number;
  unsupportedSchemas: number;
  lifecycleAnomalies: number;
  lastKnown: LastKnownCycle | null;
}

/**
 * Why no review is being shown. Three different facts, never one word:
 * the backend could not be reached, it answered with an error, or it
 * answered with something this client cannot trust.
 */
export type CycleReviewFailure =
  | "unreachable"
  | "http_error"
  | "invalid_contract";

export interface CycleReviewResult {
  review: CycleReview | null;
  backendUrl: string;
  failure?: CycleReviewFailure;
  detail?: string;
}

export class CycleContractError extends Error {}

function fail(field: string, saw: unknown): never {
  throw new CycleContractError(
    `"${field}" is not valid in the /cycle/latest response (saw ${typeof saw}).`,
  );
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    fail(field, value);
  }

  return value as Record<string, unknown>;
}

function requiredString(source: Record<string, unknown>, field: string): string {
  const value = source[field];

  if (typeof value !== "string") {
    fail(field, value);
  }

  return value;
}

function requiredBoolean(
  source: Record<string, unknown>,
  field: string,
): boolean {
  const value = source[field];

  if (typeof value !== "boolean") {
    fail(field, value);
  }

  return value;
}

function requiredCount(source: Record<string, unknown>, field: string): number {
  const value = source[field];

  if (typeof value !== "number" || !Number.isInteger(value) || value < 0) {
    fail(field, value);
  }

  return value;
}

function nullableNumber(
  source: Record<string, unknown>,
  field: string,
): number | null {
  const value = source[field];

  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value !== "number" || !Number.isFinite(value)) {
    fail(field, value);
  }

  return value;
}

function nullableString(
  source: Record<string, unknown>,
  field: string,
): string | null {
  const value = source[field];

  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value !== "string") {
    fail(field, value);
  }

  return value;
}

/** A timestamp the backend may omit, but may never send unparseable. */
function nullableTimestamp(
  source: Record<string, unknown>,
  field: string,
): string | null {
  const value = nullableString(source, field);

  if (value === null) {
    return null;
  }

  if (Number.isNaN(new Date(value).getTime())) {
    fail(field, value);
  }

  return value;
}

function requiredTimestamp(
  source: Record<string, unknown>,
  field: string,
): string {
  const value = requiredString(source, field);

  if (Number.isNaN(new Date(value).getTime())) {
    fail(field, value);
  }

  return value;
}

function requiredStrings(
  source: Record<string, unknown>,
  field: string,
): string[] {
  const value = source[field];

  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    fail(field, value);
  }

  return value as string[];
}

function envelopeOf(raw: unknown, field: string): CycleEnvelope | null {
  if (raw === null || raw === undefined) {
    return null;
  }

  const item = object(raw, field);

  return {
    kind: requiredString(item, "kind"),
    stated: requiredString(item, "stated"),
    policySource: requiredString(item, "policy_source"),
    policyVersion: requiredString(item, "policy_version"),
    evidenceCeiling: requiredString(item, "evidence_ceiling"),
    capacityCeilingPct: nullableNumber(item, "capacity_ceiling_pct"),
    finalPct: nullableNumber(item, "final_pct"),
    bindingConstraint: requiredString(item, "binding_constraint"),
    because: requiredString(item, "because"),
    namedGaps: requiredStrings(item, "named_gaps"),
    qualityAuthority: nullableString(item, "quality_authority"),
    starterCapped: requiredBoolean(item, "starter_capped"),
    priceAsOf: requiredString(item, "price_as_of"),
    portfolioAsOf: requiredString(item, "portfolio_as_of"),
    liquidity: requiredString(item, "liquidity"),
  };
}

function courseOf(raw: unknown, field: string): CycleCourse {
  const item = object(raw, field);

  return {
    symbol: requiredString(item, "symbol"),
    disposition: requiredString(item, "disposition"),
    rationale: requiredString(item, "rationale"),
    conviction: nullableNumber(item, "conviction"),
    evidenceAsOf: requiredString(item, "evidence_as_of"),
    actionKind: requiredString(item, "action_kind"),
    actionStatement: requiredString(item, "action_statement"),
    actionBecause: requiredString(item, "action_because"),
    asksForSomething: requiredBoolean(item, "asks_for_something"),
    envelope: envelopeOf(item.envelope, `${field}.envelope`),
  };
}

function coursesOf(source: Record<string, unknown>, field: string): CycleCourse[] {
  const value = source[field];

  if (!Array.isArray(value)) {
    fail(field, value);
  }

  return value.map((raw, index) => courseOf(raw, `${field}[${index}]`));
}

export function parseCycleReview(payload: unknown): CycleReview {
  const body = object(payload, "response");

  const execution = requiredString(body, "execution");

  if (!(CYCLE_EXECUTIONS as readonly string[]).includes(execution)) {
    fail("execution", execution);
  }

  const comparisonRaw = nullableString(body, "comparison_outcome");

  if (
    comparisonRaw !== null &&
    !(COMPARISON_OUTCOMES as readonly string[]).includes(comparisonRaw)
  ) {
    fail("comparison_outcome", comparisonRaw);
  }

  const lastKnownRaw = body.last_known;
  let lastKnown: LastKnownCycle | null = null;

  if (lastKnownRaw !== null && lastKnownRaw !== undefined) {
    const item = object(lastKnownRaw, "last_known");

    lastKnown = {
      cycleId: requiredString(item, "cycle_id"),
      finishedAt: requiredTimestamp(item, "finished_at"),
      status: requiredString(item, "status"),
      courses: coursesOf(item, "courses"),
    };
  }

  const stagesRaw = body.stages;

  if (!Array.isArray(stagesRaw)) {
    fail("stages", stagesRaw);
  }

  return {
    execution: execution as CycleExecution,
    cycleId: nullableString(body, "cycle_id"),
    startedAt: nullableTimestamp(body, "started_at"),
    finishedAt: nullableTimestamp(body, "finished_at"),
    stages: stagesRaw.map((raw, index) => {
      const item = object(raw, `stages[${index}]`);

      return {
        name: requiredString(item, "name"),
        outcome: requiredString(item, "outcome"),
        because: requiredString(item, "because"),
      };
    }),
    comparisonOutcome: comparisonRaw as ComparisonOutcome | null,
    comparisonPriorCycleId: requiredString(body, "comparison_prior_cycle_id"),
    comparisonBecause: requiredString(body, "comparison_because"),
    securitiesAsked: requiredCount(body, "securities_asked"),
    securitiesPriced: requiredCount(body, "securities_priced"),
    refusals: requiredStrings(body, "refusals"),
    newlyProduced: requiredStrings(body, "newly_produced"),
    changed: requiredStrings(body, "changed"),
    unchanged: requiredStrings(body, "unchanged"),
    attention: requiredStrings(body, "attention"),
    courses: coursesOf(body, "courses"),
    // Carried, never substituted. Null means the domain did not permit
    // the sentence, and no weaker phrase stands in for it.
    noActionSuggested: nullableString(body, "no_action_suggested"),
    streamComplete: requiredBoolean(body, "stream_complete"),
    unreadableRecords: requiredCount(body, "unreadable_records"),
    unsupportedSchemas: requiredCount(body, "unsupported_schemas"),
    lifecycleAnomalies: requiredCount(body, "lifecycle_anomalies"),
    lastKnown,
  };
}

export async function getCycleReview(): Promise<CycleReviewResult> {
  const endpoint = `${BACKEND_URL}/cycle/latest`;

  let response: Response;

  try {
    response = await fetch(endpoint, { cache: "no-store" });
  } catch (error) {
    return {
      review: null,
      backendUrl: endpoint,
      failure: "unreachable",
      detail: error instanceof Error ? error.message : "Unknown error",
    };
  }

  if (!response.ok) {
    return {
      review: null,
      backendUrl: endpoint,
      failure: "http_error",
      detail: `The backend answered ${response.status}.`,
    };
  }

  try {
    return {
      review: parseCycleReview(await response.json()),
      backendUrl: endpoint,
    };
  } catch (error) {
    // A readable response this client cannot trust is its own fact. It
    // is not "the backend is unreachable", and it is certainly not an
    // empty review.
    return {
      review: null,
      backendUrl: endpoint,
      failure: "invalid_contract",
      detail: error instanceof Error ? error.message : "Unknown error",
    };
  }
}
