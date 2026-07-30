import { executiveWorkspaceMock } from "@/lib/mocks/executive-workspace";
import type {
  ExecutiveWorkspaceViewModel,
  PortfolioSnapshotViewModel,
} from "@/lib/view-models/executive-workspace";

const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

type UnknownRecord = Record<string, unknown>;

export interface ExecutiveWorkspaceResult {
  workspace: ExecutiveWorkspaceViewModel;
  source: "backend" | "fallback";
  backendUrl: string;
  error?: string;
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function recordAt(
  record: UnknownRecord,
  ...keys: string[]
): UnknownRecord | undefined {
  for (const key of keys) {
    const value = record[key];

    if (isRecord(value)) {
      return value;
    }
  }

  return undefined;
}

function numberAt(
  record: UnknownRecord,
  keys: readonly string[],
  fallback = 0,
): number {
  for (const key of keys) {
    const value = record[key];

    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }

    if (typeof value === "string") {
      const parsed = Number(value);

      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }

  return fallback;
}

function stringAt(
  record: UnknownRecord,
  keys: readonly string[],
  fallback: string,
): string {
  for (const key of keys) {
    const value = record[key];

    if (typeof value === "string" && value.trim().length > 0) {
      return value;
    }
  }

  return fallback;
}

function arrayLengthAt(
  record: UnknownRecord,
  keys: readonly string[],
  fallback = 0,
): number {
  for (const key of keys) {
    const value = record[key];

    if (Array.isArray(value)) {
      return value.length;
    }

    if (typeof value === "number" && Number.isFinite(value)) {
      return value;
    }
  }

  return fallback;
}

function clampScore(value: number): number {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function inferHealthScore(
  root: UnknownRecord,
  portfolio: UnknownRecord,
): number {
  const explicitScore = numberAt(
    portfolio,
    [
      "health_score",
      "healthScore",
      "portfolio_health",
      "portfolioHealth",
      "health",
    ],
    Number.NaN,
  );

  if (Number.isFinite(explicitScore)) {
    return clampScore(explicitScore);
  }

  const rootScore = numberAt(
    root,
    ["portfolio_health", "portfolioHealth"],
    Number.NaN,
  );

  if (Number.isFinite(rootScore)) {
    return clampScore(rootScore);
  }

  return 100;
}

function inferHealthLabel(score: number): string {
  if (score >= 85) return "Healthy";
  if (score >= 70) return "Stable";
  if (score >= 50) return "Needs attention";
  return "At risk";
}

function inferRiskLevel(
  portfolio: UnknownRecord,
  invested: number,
  equity: number,
): string {
  const explicitRisk = stringAt(
    portfolio,
    ["risk_level", "riskLevel", "risk"],
    "",
  );

  if (explicitRisk) {
    return explicitRisk;
  }

  if (equity <= 0 || invested <= 0) {
    return "Low";
  }

  const investedRatio = invested / equity;

  if (investedRatio < 0.35) return "Low";
  if (investedRatio < 0.75) return "Moderate";
  return "Elevated";
}

function inferDiversification(
  portfolio: UnknownRecord,
  openPositions: number,
): string {
  const explicitDiversification = stringAt(
    portfolio,
    ["diversification", "diversification_label", "diversificationLabel"],
    "",
  );

  if (explicitDiversification) {
    return explicitDiversification;
  }

  if (openPositions === 0) return "No active exposure";
  if (openPositions < 4) return "Concentrated";
  if (openPositions < 8) return "Moderate";
  return "Good";
}

function mapPortfolio(
  root: UnknownRecord,
  fallback: PortfolioSnapshotViewModel,
): PortfolioSnapshotViewModel {
  const portfolio =
    recordAt(
      root,
      "portfolio",
      "portfolio_snapshot",
      "portfolioSnapshot",
      "account",
      "account_snapshot",
      "accountSnapshot",
    ) ?? root;

  const totalEquity = numberAt(
    portfolio,
    [
      "total_equity",
      "totalEquity",
      "equity",
      "portfolio_value",
      "portfolioValue",
      "account_value",
      "accountValue",
    ],
    fallback.totalEquity,
  );

  const availableCash = numberAt(
    portfolio,
    [
      "available_cash",
      "availableCash",
      "cash",
      "cash_available",
      "cashAvailable",
      "available_balance",
      "availableBalance",
    ],
    fallback.availableCash,
  );

  const invested = numberAt(
    portfolio,
    [
      "invested",
      "invested_amount",
      "investedAmount",
      "total_invested",
      "totalInvested",
      "exposure",
    ],
    Math.max(0, totalEquity - availableCash),
  );

  const unrealizedProfitLoss = numberAt(
    portfolio,
    [
      "unrealized_pnl",
      "unrealizedPnl",
      "unrealized_profit_loss",
      "unrealizedProfitLoss",
      "profit_loss",
      "profitLoss",
      "pnl",
    ],
    fallback.unrealizedProfitLoss,
  );

  const openPositions = arrayLengthAt(
    portfolio,
    [
      "positions",
      "open_positions",
      "openPositions",
      "position_count",
      "positionCount",
    ],
    fallback.openPositions,
  );

  const pendingOrders = arrayLengthAt(
    portfolio,
    [
      "pending_orders",
      "pendingOrders",
      "orders",
      "order_count",
      "orderCount",
    ],
    fallback.pendingOrders,
  );

  const healthScore = inferHealthScore(root, portfolio);

  return {
    totalEquity,
    availableCash,
    invested,
    unrealizedProfitLoss,
    openPositions,
    pendingOrders,
    healthScore,
    healthLabel: inferHealthLabel(healthScore),
    riskLevel: inferRiskLevel(portfolio, invested, totalEquity),
    diversification: inferDiversification(portfolio, openPositions),
  };
}

export async function getExecutiveWorkspace(): Promise<ExecutiveWorkspaceResult> {
  const endpoint = `${BACKEND_URL}/brain/`;

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
        `Backend returned ${response.status}: ${responseBody.slice(0, 300)}`,
      );
    }

    const payload: unknown = await response.json();

    if (!isRecord(payload)) {
      throw new Error("The /brain response is not a JSON object.");
    }

    return {
      workspace: {
        ...executiveWorkspaceMock,
        lastReviewedAt: new Intl.DateTimeFormat("en-US", {
          weekday: "long",
          month: "long",
          day: "numeric",
          hour: "2-digit",
          minute: "2-digit",
        }).format(new Date()),
        portfolio: mapPortfolio(payload, executiveWorkspaceMock.portfolio),
      },
      source: "backend",
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      workspace: executiveWorkspaceMock,
      source: "fallback",
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
