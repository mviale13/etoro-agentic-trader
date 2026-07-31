import { executiveWorkspaceMock } from "@/lib/mocks/executive-workspace";
import type {
  ExecutiveBriefViewModel,
  ExecutivePriorityViewModel,
  ExecutiveWorkspaceViewModel,
  PortfolioSnapshotViewModel,
  PriorityUrgency,
} from "@/lib/view-models/executive-workspace";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export interface ExecutiveWorkspaceResult {
  workspace: ExecutiveWorkspaceViewModel;
  source: "backend" | "fallback";
  backendUrl: string;
  error?: string;
}

/**
 * The backend contract.
 *
 * These mirror `GET /brain/` and `GET /executive/{symbol}` exactly. The
 * dashboard never guesses at field names: if the backend renames a field the
 * parse fails loudly instead of silently substituting demo data.
 */
interface BrainPortfolioPayload {
  total_value: number;
  available_cash_usd: number;
  invested_usd: number;
  liquidity_pct: number;
  positions: number;
}

interface BrainPayload {
  portfolio: BrainPortfolioPayload;
  recommendation: {
    symbol: string;
  };
}

interface ExecutiveBriefPayload {
  symbol: string;
  headline: string;
  summary: string;
  confidence: number;
  portfolio_health: number;
  priorities: readonly {
    title: string;
    description: string;
    urgency: number;
  }[];
}

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
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new Error(`Expected a string at "${field}", received ${typeof value}`);
  }

  return value;
}

function parseBrain(payload: unknown): BrainPayload {
  if (!isRecord(payload)) {
    throw new Error("The /brain response is not a JSON object.");
  }

  const portfolio = payload.portfolio;

  if (!isRecord(portfolio)) {
    throw new Error("The /brain response has no portfolio object.");
  }

  const recommendation = payload.recommendation;

  if (!isRecord(recommendation)) {
    throw new Error("The /brain response has no recommendation object.");
  }

  return {
    portfolio: {
      total_value: requireNumber(portfolio.total_value, "portfolio.total_value"),
      available_cash_usd: requireNumber(
        portfolio.available_cash_usd,
        "portfolio.available_cash_usd",
      ),
      invested_usd: requireNumber(
        portfolio.invested_usd,
        "portfolio.invested_usd",
      ),
      liquidity_pct: requireNumber(
        portfolio.liquidity_pct,
        "portfolio.liquidity_pct",
      ),
      positions: requireNumber(portfolio.positions, "portfolio.positions"),
    },
    recommendation: {
      symbol: requireString(recommendation.symbol, "recommendation.symbol"),
    },
  };
}

function parseExecutiveBrief(payload: unknown): ExecutiveBriefPayload {
  if (!isRecord(payload)) {
    throw new Error("The /executive response is not a JSON object.");
  }

  const priorities = Array.isArray(payload.priorities) ? payload.priorities : [];

  return {
    symbol: requireString(payload.symbol, "symbol"),
    headline: requireString(payload.headline, "headline"),
    summary: requireString(payload.summary, "summary"),
    confidence: requireNumber(payload.confidence, "confidence"),
    portfolio_health: requireNumber(
      payload.portfolio_health,
      "portfolio_health",
    ),
    priorities: priorities.filter(isRecord).map((priority, index) => ({
      title: requireString(priority.title, `priorities[${index}].title`),
      description: requireString(
        priority.description,
        `priorities[${index}].description`,
      ),
      urgency: requireNumber(priority.urgency, `priorities[${index}].urgency`),
    })),
  };
}

function healthLabel(score: number): string {
  if (score >= 85) return "Healthy";
  if (score >= 70) return "Stable";
  if (score >= 50) return "Needs attention";
  return "At risk";
}

function riskLevel(invested: number, equity: number): string {
  if (equity <= 0 || invested <= 0) {
    return "Low";
  }

  const investedRatio = invested / equity;

  if (investedRatio < 0.35) return "Low";
  if (investedRatio < 0.75) return "Moderate";
  return "Elevated";
}

function diversification(openPositions: number): string {
  if (openPositions === 0) return "No active exposure";
  if (openPositions < 4) return "Concentrated";
  if (openPositions < 8) return "Moderate";
  return "Good";
}

/** Presentation banding only — the backend owns the underlying score. */
function urgencyBand(urgency: number): PriorityUrgency {
  if (urgency >= 0.6) return "now";
  if (urgency >= 0.3) return "today";
  return "monitor";
}

function mapPortfolio(
  brain: BrainPayload,
  brief: ExecutiveBriefPayload,
): PortfolioSnapshotViewModel {
  const totalEquity = brain.portfolio.total_value;
  const invested = brain.portfolio.invested_usd;
  const openPositions = brain.portfolio.positions;

  const healthScore = Math.max(
    0,
    Math.min(100, Math.round(brief.portfolio_health * 100)),
  );

  return {
    totalEquity,
    availableCash: brain.portfolio.available_cash_usd,
    invested,
    // The backend does not publish these yet; showing a demo number here
    // would misrepresent the account.
    unrealizedProfitLoss: null,
    openPositions,
    pendingOrders: null,
    healthScore,
    healthLabel: healthLabel(healthScore),
    riskLevel: riskLevel(invested, totalEquity),
    diversification: diversification(openPositions),
  };
}

function mapPriorities(
  brief: ExecutiveBriefPayload,
): ExecutivePriorityViewModel[] {
  return brief.priorities.map((priority, index) => ({
    id: `${brief.symbol}-priority-${index}`,
    urgency: urgencyBand(priority.urgency),
    title: priority.title,
    rationale: priority.description,
  }));
}

function mapBrief(brief: ExecutiveBriefPayload): ExecutiveBriefViewModel {
  return {
    symbol: brief.symbol,
    headline: brief.headline,
    summary: brief.summary,
    confidence: brief.confidence,
  };
}

async function fetchJson(endpoint: string): Promise<unknown> {
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

  return response.json();
}

export async function getExecutiveWorkspace(): Promise<ExecutiveWorkspaceResult> {
  const brainEndpoint = `${BACKEND_URL}/brain/`;

  try {
    const brain = parseBrain(await fetchJson(brainEndpoint));

    const briefEndpoint = `${BACKEND_URL}/executive/${encodeURIComponent(
      brain.recommendation.symbol,
    )}`;

    const brief = parseExecutiveBrief(await fetchJson(briefEndpoint));

    return {
      workspace: {
        lastReviewedAt: new Intl.DateTimeFormat("en-US", {
          weekday: "long",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }).format(new Date()),
        situation: "stable",
        portfolio: mapPortfolio(brain, brief),
        brief: mapBrief(brief),
        // No backend source for the change feed yet, so the dashboard shows
        // nothing rather than demo entries.
        changes: [],
        priorities: mapPriorities(brief),
      },
      source: "backend",
      backendUrl: brainEndpoint,
    };
  } catch (error) {
    return {
      workspace: executiveWorkspaceMock,
      source: "fallback",
      backendUrl: brainEndpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
