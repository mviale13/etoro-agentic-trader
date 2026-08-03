const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

type UnknownRecord = Record<string, unknown>;

/**
 * The account's own worst fall, measured off its daily balances.
 *
 * Null on the overview when the Brain reports it unmeasured. The page
 * renders that absence rather than a zero: an account that never fell and
 * an account whose history nobody could read are not the same account.
 */
export interface PortfolioDrawdown {
  depthPct: number;
  currentDepthPct: number;
  recovered: boolean;
  peakOn: string;
  troughOn: string;
  startsOn: string;
  endsOn: string;
  observations: number;
  reading: string;
}

export interface PortfolioOverview {
  totalValueUsd: number;
  totalValueEur: number;
  availableCashUsd: number;
  availableCashEur: number;
  investedUsd: number;
  investedEur: number;
  liquidityPct: number;
  positions: number;
  lastSync: string | null;
  observationTitle: string;
  observationMessage: string;
  drawdown: PortfolioDrawdown | null;
}

export interface PortfolioOverviewResult {
  portfolio: PortfolioOverview | null;
  source: "backend" | "unavailable";
  backendUrl: string;
  error?: string;
}

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function numberValue(
  record: UnknownRecord,
  key: string,
  fallback = 0,
): number {
  const value = record[key];

  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  return fallback;
}

function stringValue(
  record: UnknownRecord,
  key: string,
  fallback = "",
): string {
  const value = record[key];

  if (typeof value === "string" && value.trim()) {
    return value;
  }

  return fallback;
}

function drawdownValue(portfolio: UnknownRecord): PortfolioDrawdown | null {
  const drawdown = portfolio.drawdown;

  if (!isRecord(drawdown)) {
    return null;
  }

  const peakOn = stringValue(drawdown, "peak_on");
  const troughOn = stringValue(drawdown, "trough_on");

  // A fall with no dates is not a measurement of a window, and the window
  // is the whole claim. Rather than render it half-stated, treat it as
  // absent — which the page already knows how to say.
  if (!peakOn || !troughOn) {
    return null;
  }

  return {
    depthPct: numberValue(drawdown, "depth_pct"),
    currentDepthPct: numberValue(drawdown, "current_depth_pct"),
    recovered: drawdown.recovered === true,
    peakOn,
    troughOn,
    startsOn: stringValue(drawdown, "starts_on"),
    endsOn: stringValue(drawdown, "ends_on"),
    observations: numberValue(drawdown, "observations"),
    reading: stringValue(drawdown, "reading", "eToro"),
  };
}

export async function getPortfolioOverview(): Promise<PortfolioOverviewResult> {
  const endpoint = `${BACKEND_URL}/brain/`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      const body = await response.text();

      throw new Error(
        `Backend returned ${response.status}: ${body.slice(0, 300)}`,
      );
    }

    const payload: unknown = await response.json();

    if (!isRecord(payload)) {
      throw new Error("The /brain response is not a JSON object.");
    }

    const portfolio = payload.portfolio;
    const observation = payload.observation;

    if (!isRecord(portfolio)) {
      throw new Error("The /brain response has no portfolio object.");
    }

    const observationRecord = isRecord(observation) ? observation : {};

    return {
      portfolio: {
        totalValueUsd: numberValue(portfolio, "total_value"),
        totalValueEur: numberValue(portfolio, "total_value_eur"),
        availableCashUsd: numberValue(portfolio, "available_cash_usd"),
        availableCashEur: numberValue(portfolio, "available_cash_eur"),
        investedUsd: numberValue(portfolio, "invested_usd"),
        investedEur: numberValue(portfolio, "invested_eur"),
        liquidityPct: numberValue(portfolio, "liquidity_pct"),
        positions: numberValue(portfolio, "positions"),
        lastSync: stringValue(portfolio, "last_sync") || null,
        observationTitle: stringValue(
          observationRecord,
          "title",
          "Portfolio observation unavailable",
        ),
        observationMessage: stringValue(
          observationRecord,
          "message",
          "MOVRvest has not produced a portfolio observation yet.",
        ),
        drawdown: drawdownValue(portfolio),
      },
      source: "backend",
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      portfolio: null,
      source: "unavailable",
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
