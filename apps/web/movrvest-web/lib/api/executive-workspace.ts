import { executiveWorkspaceMock } from "@/lib/mocks/executive-workspace";
import type {
  ChangeSeverity,
  ExecutiveBriefViewModel,
  ExecutiveChangeViewModel,
  ExecutivePriorityViewModel,
  ExecutiveWorkspaceViewModel,
  PortfolioSnapshotViewModel,
  PriorityUrgency,
} from "@/lib/view-models/executive-workspace";
import type {
  ConvictionLevel,
  RankedInvestmentCaseViewModel,
} from "@/lib/view-models/investment-case";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

export interface ExecutiveWorkspaceResult {
  workspace: ExecutiveWorkspaceViewModel;
  investmentCases: readonly RankedInvestmentCaseViewModel[];
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
  pending_orders: number;
  unrealized_pnl_usd: number;
}

interface BrainPayload {
  portfolio: BrainPortfolioPayload;
}

interface PriorityPayload {
  title: string;
  description: string;
  urgency: number;
}

interface RankedCasePayload {
  rank: number;
  symbol: string;
  recommendation: string;
  conviction: number;
  committee_agreement: number;
  risk_level: string;
  summary: string;
  why_now: readonly string[];
  risks: readonly string[];
  expected_holding_period: string;
  previous_decisions: string | null;
}

interface ChangePayload {
  title: string;
  description: string;
  category: string;
  severity: string;
  timestamp: string;
  action_required: boolean;
}

interface PortfolioBriefingPayload {
  headline: string;
  summary: string;
  confidence: number;
  portfolio_health: number;
  priorities: readonly PriorityPayload[];
  investment_cases: readonly RankedCasePayload[];
  changes: readonly ChangePayload[];
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

/**
 * Read a field the backend reports as absent when it has nothing to say.
 *
 * Null stays null: an absent value is never replaced with a placeholder.
 */
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

function parseBrain(payload: unknown): BrainPayload {
  if (!isRecord(payload)) {
    throw new Error("The /brain response is not a JSON object.");
  }

  const portfolio = payload.portfolio;

  if (!isRecord(portfolio)) {
    throw new Error("The /brain response has no portfolio object.");
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
      pending_orders: requireNumber(
        portfolio.pending_orders,
        "portfolio.pending_orders",
      ),
      unrealized_pnl_usd: requireNumber(
        portfolio.unrealized_pnl_usd,
        "portfolio.unrealized_pnl_usd",
      ),
    },
  };
}

function parsePortfolioBriefing(payload: unknown): PortfolioBriefingPayload {
  if (!isRecord(payload)) {
    throw new Error("The /executive/portfolio response is not a JSON object.");
  }

  const priorities = Array.isArray(payload.priorities) ? payload.priorities : [];
  const cases = Array.isArray(payload.investment_cases)
    ? payload.investment_cases
    : [];
  const changes = Array.isArray(payload.changes) ? payload.changes : [];

  return {
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
    investment_cases: cases.filter(isRecord).map((item, index) => ({
      rank: requireNumber(item.rank, `investment_cases[${index}].rank`),
      symbol: requireString(item.symbol, `investment_cases[${index}].symbol`),
      recommendation: requireString(
        item.recommendation,
        `investment_cases[${index}].recommendation`,
      ),
      conviction: requireNumber(
        item.conviction,
        `investment_cases[${index}].conviction`,
      ),
      committee_agreement: requireNumber(
        item.committee_agreement,
        `investment_cases[${index}].committee_agreement`,
      ),
      risk_level: requireString(
        item.risk_level,
        `investment_cases[${index}].risk_level`,
      ),
      summary: requireString(item.summary, `investment_cases[${index}].summary`),
      why_now: Array.isArray(item.why_now)
        ? item.why_now.filter((value): value is string => typeof value === "string")
        : [],
      risks: Array.isArray(item.risks)
        ? item.risks.filter((value): value is string => typeof value === "string")
        : [],
      expected_holding_period: requireString(
        item.expected_holding_period,
        `investment_cases[${index}].expected_holding_period`,
      ),
      previous_decisions: optionalString(
        item.previous_decisions,
        `investment_cases[${index}].previous_decisions`,
      ),
    })),
    changes: changes.filter(isRecord).map((change, index) => ({
      title: requireString(change.title, `changes[${index}].title`),
      description: requireString(
        change.description,
        `changes[${index}].description`,
      ),
      category: requireString(change.category, `changes[${index}].category`),
      severity: requireString(change.severity, `changes[${index}].severity`),
      timestamp: requireString(change.timestamp, `changes[${index}].timestamp`),
      action_required: change.action_required === true,
    })),
  };
}

function convictionLevel(conviction: number): ConvictionLevel {
  if (conviction >= 85) return "Very High Conviction";
  if (conviction >= 70) return "High Conviction";
  if (conviction >= 50) return "Moderate Conviction";
  return "Low Conviction";
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function mapInvestmentCases(
  briefing: PortfolioBriefingPayload,
): RankedInvestmentCaseViewModel[] {
  return briefing.investment_cases.map((item) => ({
    rank: item.rank,
    symbol: item.symbol,
    recommendation: item.recommendation,
    conviction: item.conviction,
    convictionLevel: convictionLevel(item.conviction),
    committeeAgreement: item.committee_agreement,
    riskLevel: titleCase(item.risk_level.replace(/_/g, " ")),
    summary: item.summary,
    whyNow: item.why_now,
    risks: item.risks,
    expectedHoldingPeriod: item.expected_holding_period,
    previousDecisions: item.previous_decisions,
    dossierHref: `/dossiers/${encodeURIComponent(item.symbol)}`,
  }));
}

/**
 * The backend measures severity as how far a decision moved along the
 * investment-case lifecycle. The dashboard only renames it.
 */
function changeSeverity(severity: string): ChangeSeverity {
  if (severity === "high") return "important";
  if (severity === "medium") return "attention";
  return "information";
}

function mapChanges(
  briefing: PortfolioBriefingPayload,
): ExecutiveChangeViewModel[] {
  return briefing.changes.map((change) => ({
    id: `${change.timestamp}-${change.title}`,
    severity: changeSeverity(change.severity),
    title: change.title,
    detail: change.description,
    context: `Recorded ${new Intl.DateTimeFormat("en-US", {
      month: "long",
      day: "numeric",
    }).format(new Date(change.timestamp))}`,
  }));
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
  briefing: PortfolioBriefingPayload,
): PortfolioSnapshotViewModel {
  const totalEquity = brain.portfolio.total_value;
  const invested = brain.portfolio.invested_usd;
  const openPositions = brain.portfolio.positions;

  const healthScore = Math.max(
    0,
    Math.min(100, Math.round(briefing.portfolio_health * 100)),
  );

  return {
    totalEquity,
    availableCash: brain.portfolio.available_cash_usd,
    invested,
    unrealizedProfitLoss: brain.portfolio.unrealized_pnl_usd,
    openPositions,
    pendingOrders: brain.portfolio.pending_orders,
    healthScore,
    healthLabel: healthLabel(healthScore),
    riskLevel: riskLevel(invested, totalEquity),
    diversification: diversification(openPositions),
  };
}

function mapPriorities(
  briefing: PortfolioBriefingPayload,
): ExecutivePriorityViewModel[] {
  return briefing.priorities.map((priority, index) => ({
    id: `${priority.title}-${index}`,
    urgency: urgencyBand(priority.urgency),
    title: priority.title,
    rationale: priority.description,
  }));
}

function mapBrief(
  briefing: PortfolioBriefingPayload,
): ExecutiveBriefViewModel {
  return {
    symbol: "Portfolio",
    headline: briefing.headline,
    summary: briefing.summary,
    confidence: briefing.confidence,
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
    const [brainPayload, briefingPayload] = await Promise.all([
      fetchJson(brainEndpoint),
      fetchJson(`${BACKEND_URL}/executive/portfolio`),
    ]);

    const brain = parseBrain(brainPayload);
    const briefing = parsePortfolioBriefing(briefingPayload);

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
        portfolio: mapPortfolio(brain, briefing),
        brief: mapBrief(briefing),
        // Decision changes the Artificial CIO actually recorded. An empty
        // feed means it has not changed its mind, not that nothing is known.
        changes: mapChanges(briefing),
        priorities: mapPriorities(briefing),
      },
      investmentCases: mapInvestmentCases(briefing),
      source: "backend",
      backendUrl: brainEndpoint,
    };
  } catch (error) {
    return {
      workspace: executiveWorkspaceMock,
      // No demo investment cases: an unreachable backend means we know
      // nothing about the holdings, and inventing cases would be worse than
      // showing none.
      investmentCases: [],
      source: "fallback",
      backendUrl: brainEndpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
