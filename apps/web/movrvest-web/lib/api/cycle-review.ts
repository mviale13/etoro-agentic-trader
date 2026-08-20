/**
 * The latest recorded CIO cycle, read from `GET /cycle/latest`.
 *
 * The homepage used to read its courses from `/executive/portfolio`,
 * which builds a Brain, runs the executive pipeline and appends journal
 * entries — during the page request. Opening the page therefore *made*
 * decisions, and two visits could disagree for reasons that had nothing
 * to do with the account.
 *
 * This client reads a record instead. Every semantic decision is
 * already made server-side: the states are typed, the sentences are the
 * domain's own, and nothing here composes a claim out of parts.
 */

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

/** What happened to the latest recorded attempt. Mirrors the backend enum. */
export type CycleExecution =
  | "none_recorded"
  | "interrupted"
  | "failed"
  | "partial"
  | "complete";

/** What the change comparison rested on, or null where none was recorded. */
export type ComparisonOutcome = "initial_baseline" | "compared" | "refused";

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

export interface CycleReviewResult {
  review: CycleReview | null;
  backendUrl: string;
  error?: string;
}

function str(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function num(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function optionalNum(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function strings(value: unknown): string[] {
  return Array.isArray(value) ? value.map(str).filter(Boolean) : [];
}

function envelopeOf(raw: unknown): CycleEnvelope | null {
  if (raw === null || typeof raw !== "object") {
    return null;
  }

  const item = raw as Record<string, unknown>;

  return {
    kind: str(item.kind),
    stated: str(item.stated),
    policySource: str(item.policy_source),
    policyVersion: str(item.policy_version),
    evidenceCeiling: str(item.evidence_ceiling),
    capacityCeilingPct: optionalNum(item.capacity_ceiling_pct),
    finalPct: optionalNum(item.final_pct),
    bindingConstraint: str(item.binding_constraint),
    because: str(item.because),
    namedGaps: strings(item.named_gaps),
    qualityAuthority:
      typeof item.quality_authority === "string" ? item.quality_authority : null,
    starterCapped: item.starter_capped === true,
    priceAsOf: str(item.price_as_of),
    portfolioAsOf: str(item.portfolio_as_of),
    liquidity: str(item.liquidity),
  };
}

function courseOf(raw: unknown): CycleCourse {
  const item = (raw ?? {}) as Record<string, unknown>;

  return {
    symbol: str(item.symbol),
    disposition: str(item.disposition),
    rationale: str(item.rationale),
    conviction: optionalNum(item.conviction),
    evidenceAsOf: str(item.evidence_as_of),
    actionKind: str(item.action_kind),
    actionStatement: str(item.action_statement),
    actionBecause: str(item.action_because),
    asksForSomething: item.asks_for_something === true,
    envelope: envelopeOf(item.envelope),
  };
}

function coursesOf(raw: unknown): CycleCourse[] {
  return Array.isArray(raw) ? raw.map(courseOf) : [];
}

export function parseCycleReview(payload: unknown): CycleReview {
  if (payload === null || typeof payload !== "object") {
    throw new Error("The /cycle/latest response is not a JSON object.");
  }

  const body = payload as Record<string, unknown>;
  const execution = str(body.execution) as CycleExecution;

  const lastKnownRaw = body.last_known;
  const lastKnown =
    lastKnownRaw && typeof lastKnownRaw === "object"
      ? ((): LastKnownCycle => {
          const item = lastKnownRaw as Record<string, unknown>;

          return {
            cycleId: str(item.cycle_id),
            finishedAt: str(item.finished_at),
            status: str(item.status),
            courses: coursesOf(item.courses),
          };
        })()
      : null;

  return {
    execution,
    cycleId: typeof body.cycle_id === "string" ? body.cycle_id : null,
    startedAt: typeof body.started_at === "string" ? body.started_at : null,
    finishedAt: typeof body.finished_at === "string" ? body.finished_at : null,
    stages: Array.isArray(body.stages)
      ? body.stages.map((raw) => {
          const item = (raw ?? {}) as Record<string, unknown>;

          return {
            name: str(item.name),
            outcome: str(item.outcome),
            because: str(item.because),
          };
        })
      : [],
    comparisonOutcome:
      typeof body.comparison_outcome === "string"
        ? (body.comparison_outcome as ComparisonOutcome)
        : null,
    comparisonPriorCycleId: str(body.comparison_prior_cycle_id),
    comparisonBecause: str(body.comparison_because),
    securitiesAsked: num(body.securities_asked),
    securitiesPriced: num(body.securities_priced),
    refusals: strings(body.refusals),
    newlyProduced: strings(body.newly_produced),
    changed: strings(body.changed),
    unchanged: strings(body.unchanged),
    attention: strings(body.attention),
    courses: coursesOf(body.courses),
    // Carried, never substituted. A null here means the domain did not
    // permit the sentence, and no weaker phrase stands in for it.
    noActionSuggested:
      typeof body.no_action_suggested === "string"
        ? body.no_action_suggested
        : null,
    streamComplete: body.stream_complete !== false,
    unreadableRecords: num(body.unreadable_records),
    unsupportedSchemas: num(body.unsupported_schemas),
    lifecycleAnomalies: num(body.lifecycle_anomalies),
    lastKnown,
  };
}

export async function getCycleReview(): Promise<CycleReviewResult> {
  const endpoint = `${BACKEND_URL}/cycle/latest`;

  try {
    const response = await fetch(endpoint, { cache: "no-store" });

    if (!response.ok) {
      return {
        review: null,
        backendUrl: endpoint,
        error: `The backend answered ${response.status}.`,
      };
    }

    return {
      review: parseCycleReview(await response.json()),
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      review: null,
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown error",
    };
  }
}
