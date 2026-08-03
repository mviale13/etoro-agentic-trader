import type {
  ResearchCandidateViewModel,
  ResearchFunnelViewModel,
  ResearchPipelineViewModel,
} from "@/lib/view-models/research";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export interface ResearchResult {
  pipeline: ResearchPipelineViewModel | null;
  backendUrl: string;
  error?: string;
}

/**
 * The backend contract.
 *
 * This mirrors `GET /research/candidates` exactly. The page never guesses at
 * field names: if the backend renames one the parse fails loudly instead of
 * quietly showing an empty pipeline that looks like a real "no candidates".
 */
function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requireNumber(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throw new Error(`Expected a number at "${field}", received ${typeof value}`);
  }

  return value;
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string") {
    throw new Error(`Expected a string at "${field}", received ${typeof value}`);
  }

  return value;
}

/** Null stays null: an absent value is never replaced with a placeholder. */
function optionalString(value: unknown, field: string): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  const text = requireString(value, field);

  return text.trim().length === 0 ? null : text;
}

/** An absent measurement stays absent; it is never read as a zero. */
function optionalNumber(value: unknown, field: string): number | null {
  if (value === null || value === undefined) {
    return null;
  }

  return requireNumber(value, field);
}

function stringList(value: unknown): readonly string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function parseFunnel(payload: unknown): ResearchFunnelViewModel {
  if (!isRecord(payload)) {
    throw new Error("The research response has no funnel object.");
  }

  return {
    candidates: requireNumber(payload.candidates, "funnel.candidates"),
    reviewed: requireNumber(payload.reviewed, "funnel.reviewed"),
    evidenced: requireNumber(payload.evidenced, "funnel.evidenced"),
    unevidenced: requireNumber(payload.unevidenced, "funnel.unevidenced"),
    notReviewed: requireNumber(payload.not_reviewed, "funnel.not_reviewed"),
    judged: requireNumber(payload.judged, "funnel.judged"),
    actionable: requireNumber(payload.actionable, "funnel.actionable"),
  };
}

function parseCandidate(
  payload: unknown,
  index: number,
): ResearchCandidateViewModel {
  if (!isRecord(payload)) {
    throw new Error(`candidates[${index}] is not a JSON object.`);
  }

  const at = (field: string) => `candidates[${index}].${field}`;
  const symbol = requireString(payload.symbol, at("symbol"));

  return {
    rank: requireNumber(payload.rank, at("rank")),
    symbol,
    name: requireString(payload.name, at("name")),
    source: requireString(payload.source, at("source")),
    recommendation: requireString(payload.recommendation, at("recommendation")),
    conviction: requireNumber(payload.conviction, at("conviction")),
    qualityScore: optionalNumber(payload.quality_score, at("quality_score")),
    valuationScore: optionalNumber(
      payload.valuation_score,
      at("valuation_score"),
    ),
    riskScore: optionalNumber(payload.risk_score, at("risk_score")),
    evidenceScore: requireNumber(payload.evidence_score, at("evidence_score")),
    portfolioFitScore: optionalNumber(
      payload.portfolio_fit_score,
      at("portfolio_fit_score"),
    ),
    evidenceWeighed: stringList(payload.evidence_weighed),
    whyNotYet: requireString(payload.why_not_yet, at("why_not_yet")),
    missingEvidence: stringList(payload.missing_evidence),
    catalysts: stringList(payload.catalysts),
    nextTrigger: optionalString(payload.next_trigger, at("next_trigger")),
    previousDecisions: optionalString(
      payload.previous_decisions,
      at("previous_decisions"),
    ),
    dossierHref: `/dossiers/${encodeURIComponent(symbol)}`,
  };
}

export async function getResearchPipeline(): Promise<ResearchResult> {
  const endpoint = `${BACKEND_URL}/research/candidates`;

  try {
    const response = await fetch(endpoint, { cache: "no-store" });

    if (!response.ok) {
      const body = await response.text();

      throw new Error(
        `Backend returned ${response.status} for ${endpoint}: ${body.slice(0, 300)}`,
      );
    }

    const payload: unknown = await response.json();

    if (!isRecord(payload)) {
      throw new Error("The research response is not a JSON object.");
    }

    const candidates = Array.isArray(payload.candidates)
      ? payload.candidates
      : [];

    return {
      pipeline: {
        funnel: parseFunnel(payload.funnel),
        candidates: candidates.map(parseCandidate),
      },
      backendUrl: endpoint,
    };
  } catch (error) {
    // No demo candidates. An unreachable backend means the pipeline is
    // unknown, and inventing companies to research would be worse than
    // showing none.
    return {
      pipeline: null,
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
