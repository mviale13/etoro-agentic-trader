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
  /**
   * Null when the backend was unreachable. An unreachable backend means
   * nothing is known about the account, and a demo workspace with plausible
   * figures would read as a measurement — so nothing is what is shown.
   */
  workspace: ExecutiveWorkspaceViewModel | null;
  investmentCases: readonly RankedInvestmentCaseViewModel[];
  source: "backend" | "unavailable";
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
  largest_position: string | null;
  largest_position_pct: number | null;
}

/**
 * The Brain's risk assessment, or null where none could be measured.
 *
 * The level is the backend's word, not a banding this dashboard performs.
 */
interface BrainRiskPayload {
  level: string | null;
}

interface BrainPayload {
  portfolio: BrainPortfolioPayload;
  risk: BrainRiskPayload | null;
}

interface PriorityPayload {
  title: string;
  description: string;
  urgency: number;
  urgency_band: string;
}

interface RankedCasePayload {
  rank: number;
  symbol: string;
  recommendation: string;
  conviction: number;
  conviction_label: string;
  committee_agreement: number;
  safety_score: number | null;
  summary: string;
  why_now: readonly string[];
  risks: readonly string[];
  expected_holding_period: string;
  trend: { direction: string; stated: string } | null;
  action: {
    kind: string;
    statement: string;
    because: string;
    checkpoint: string | null;
  } | null;
  conviction_change: {
    previous: number;
    delta: number;
    stated: string;
    because: readonly string[];
    unexplained: boolean;
  } | null;
}

interface ChangePayload {
  title: string;
  description: string;
  category: string;
  severity: string;
  timestamp: string;
  action_required: boolean;
}

interface TodayBriefingPayload {
  lines: readonly { statement: string; notable: boolean }[];
  headline: string | null;
  is_quiet: boolean;
}

interface PortfolioBriefingPayload {
  today: TodayBriefingPayload;
  headline: string;
  summary: string;
  confidence: number | null;
  portfolio_health: number;
  portfolio_health_label: string;
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

/** A number the platform may not have been able to measure. */
function optionalNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
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

  // Null when the Brain could not assess risk. The distinction between a
  // low risk and an unmeasured one is kept, never papered over.
  const risk = isRecord(payload.risk)
    ? { level: optionalString(payload.risk.level, "risk.level") }
    : null;

  return {
    risk,
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
      largest_position: optionalString(
        portfolio.largest_position,
        "portfolio.largest_position",
      ),
      largest_position_pct: optionalNumber(portfolio.largest_position_pct),
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

  const today = payload.today;

  if (!isRecord(today)) {
    throw new Error("The /executive/portfolio response has no today briefing.");
  }

  const lines = Array.isArray(today.lines) ? today.lines : [];

  return {
    today: {
      lines: lines.filter(isRecord).map((line, index) => ({
        statement: requireString(line.statement, `today.lines[${index}]`),
        notable: line.notable === true,
      })),
      headline: optionalString(today.headline, "today.headline"),
      is_quiet: today.is_quiet === true,
    },
    headline: requireString(payload.headline, "headline"),
    summary: requireString(payload.summary, "summary"),
    confidence: optionalNumber(payload.confidence),
    portfolio_health: requireNumber(
      payload.portfolio_health,
      "portfolio_health",
    ),
    portfolio_health_label: requireString(
      payload.portfolio_health_label,
      "portfolio_health_label",
    ),
    priorities: priorities.filter(isRecord).map((priority, index) => ({
      title: requireString(priority.title, `priorities[${index}].title`),
      description: requireString(
        priority.description,
        `priorities[${index}].description`,
      ),
      urgency: requireNumber(priority.urgency, `priorities[${index}].urgency`),
      urgency_band: requireString(
        priority.urgency_band,
        `priorities[${index}].urgency_band`,
      ),
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
      conviction_label: requireString(
        item.conviction_label,
        `investment_cases[${index}].conviction_label`,
      ),
      committee_agreement: requireNumber(
        item.committee_agreement,
        `investment_cases[${index}].committee_agreement`,
      ),
      safety_score: optionalNumber(item.safety_score),
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
      trend: isRecord(item.trend)
        ? {
            direction: requireString(
              item.trend.direction,
              `investment_cases[${index}].trend.direction`,
            ),
            stated: requireString(
              item.trend.stated,
              `investment_cases[${index}].trend.stated`,
            ),
          }
        : null,
      conviction_change: isRecord(item.conviction_change)
        ? {
            previous: requireNumber(
              item.conviction_change.previous,
              `investment_cases[${index}].conviction_change.previous`,
            ),
            delta: requireNumber(
              item.conviction_change.delta,
              `investment_cases[${index}].conviction_change.delta`,
            ),
            stated: requireString(
              item.conviction_change.stated,
              `investment_cases[${index}].conviction_change.stated`,
            ),
            because: Array.isArray(item.conviction_change.because)
              ? item.conviction_change.because.filter(
                  (value): value is string => typeof value === "string",
                )
              : [],
            unexplained: item.conviction_change.unexplained === true,
          }
        : null,
      action: isRecord(item.action)
        ? {
            kind: requireString(
              item.action.kind,
              `investment_cases[${index}].action.kind`,
            ),
            statement: requireString(
              item.action.statement,
              `investment_cases[${index}].action.statement`,
            ),
            because: requireString(
              item.action.because,
              `investment_cases[${index}].action.because`,
            ),
            checkpoint: optionalString(
              item.action.checkpoint,
              `investment_cases[${index}].action.checkpoint`,
            ),
          }
        : null,
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

/**
 * The backend's conviction wording, validated against the vocabulary this
 * dashboard renders. An unknown label fails loudly instead of being guessed
 * into a band the CIO never assigned.
 */
function parseConvictionLabel(value: string, field: string): ConvictionLevel {
  const known: readonly ConvictionLevel[] = [
    "Very High Conviction",
    "High Conviction",
    "Moderate Conviction",
    "Low Conviction",
  ];

  const match = known.find((label) => label === value);

  if (!match) {
    throw new Error(`Unknown conviction label at "${field}": ${value}`);
  }

  return match;
}

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1).toLowerCase();
}

function mapInvestmentCases(
  briefing: PortfolioBriefingPayload,
): RankedInvestmentCaseViewModel[] {
  return briefing.investment_cases.map((item, index) => ({
    rank: item.rank,
    symbol: item.symbol,
    recommendation: item.recommendation,
    conviction: item.conviction,
    convictionLevel: parseConvictionLabel(
      item.conviction_label,
      `investment_cases[${index}].conviction_label`,
    ),
    committeeAgreement: item.committee_agreement,
    safetyScore: item.safety_score,
    summary: item.summary,
    whyNow: item.why_now,
    risks: item.risks,
    expectedHoldingPeriod: item.expected_holding_period,
    trend: item.trend,
    action: item.action,
    convictionChange: item.conviction_change,
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

/**
 * The backend's urgency banding, validated against the queues this
 * dashboard renders. An unknown band fails loudly instead of being guessed
 * into an urgency the CIO never assigned.
 */
function parseUrgencyBand(value: string, field: string): PriorityUrgency {
  if (value === "now" || value === "today" || value === "monitor") {
    return value;
  }

  throw new Error(`Unknown urgency band at "${field}": ${value}`);
}

function mapPortfolio(
  brain: BrainPayload,
  briefing: PortfolioBriefingPayload,
): PortfolioSnapshotViewModel {
  // Rounding a 0-1 score into "87 / 100" is formatting; the score and its
  // word both arrive from the backend.
  const healthScore = Math.max(
    0,
    Math.min(100, Math.round(briefing.portfolio_health * 100)),
  );

  return {
    totalEquity: brain.portfolio.total_value,
    availableCash: brain.portfolio.available_cash_usd,
    invested: brain.portfolio.invested_usd,
    unrealizedProfitLoss: brain.portfolio.unrealized_pnl_usd,
    openPositions: brain.portfolio.positions,
    pendingOrders: brain.portfolio.pending_orders,
    liquidityPct: brain.portfolio.liquidity_pct,
    healthScore,
    healthLabel: briefing.portfolio_health_label,
    // Null when the Brain could not assess risk — rendered as "Not
    // measured", never defaulted to a reassuring "Low".
    riskLevel: brain.risk?.level ?? null,
    largestPositionSymbol: brain.portfolio.largest_position,
    largestPositionPct: brain.portfolio.largest_position_pct,
  };
}

function mapPriorities(
  briefing: PortfolioBriefingPayload,
): ExecutivePriorityViewModel[] {
  return briefing.priorities.map((priority, index) => ({
    id: `${priority.title}-${index}`,
    urgency: parseUrgencyBand(
      priority.urgency_band,
      `priorities[${index}].urgency_band`,
    ),
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
        today: {
          lines: briefing.today.lines,
          headline: briefing.today.headline,
          isQuiet: briefing.today.is_quiet,
        },
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
    // An unreachable backend means nothing is known about the account.
    // Nothing is what is shown: no demo workspace, no demo cases. A
    // plausible figure on an investment surface reads as a measurement.
    return {
      workspace: null,
      investmentCases: [],
      source: "unavailable",
      backendUrl: brainEndpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
