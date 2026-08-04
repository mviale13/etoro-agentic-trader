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

/**
 * The four ways this account can lose money, as the Brain measured them.
 *
 * Each component is a ratio from 0 to 1, or null where it is unmeasured.
 * Null is never rendered as zero: a risk nobody could measure and a risk
 * measured at nothing are opposite findings.
 */
export interface PortfolioRisk {
  overall: number | null;
  level: string | null;
  market: number | null;
  concentration: number | null;
  liquidity: number | null;
  drawdown: number | null;
  factors: string[];
  evidence: { statement: string; source: string }[];
  unmeasured: string[];
}

/**
 * How much room the account has to act, measured in the Brain against the
 * investor's own policy. Headroom arrives signed: a largest position over
 * its limit is a negative number — a measured breach the page must state.
 */
export interface PortfolioCapacity {
  cashActualPct: number;
  cashTargetPct: number | null;
  fundingRoomPct: number | null;
  fundingRoomUsd: number | null;
  singlePositionLimitPct: number | null;
  largestPosition: string | null;
  largestPositionPct: number | null;
  singlePositionHeadroomPct: number | null;
  cryptoLimitPct: number | null;
  cryptoActualPct: number | null;
  cryptoHeadroomPct: number | null;
  unmeasured: string[];
}

/**
 * One position as the broker reported it. The weight is the snapshot's own
 * measurement and arrives ready — null when the account reports no value
 * to take a share of, which is not the same as a weight of zero.
 */
export interface PortfolioHolding {
  symbol: string;
  resolved: boolean;
  assetClass: string | null;
  investedUsd: number;
  marketValueUsd: number;
  unrealizedPnlUsd: number;
  weightPct: number | null;
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
  risk: PortfolioRisk | null;
  capacity: PortfolioCapacity | null;
  holdings: PortfolioHolding[];
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

function measuredNumber(record: UnknownRecord, key: string): number | null {
  const value = record[key];

  // Null means unmeasured and must survive as null. Falling back to zero
  // here would render "no risk" for a component nobody could measure.
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  return null;
}

function stringList(record: UnknownRecord, key: string): string[] {
  const value = record[key];

  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function riskValue(payload: UnknownRecord): PortfolioRisk | null {
  const risk = payload.risk;

  if (!isRecord(risk)) {
    return null;
  }

  const evidence = Array.isArray(risk.evidence) ? risk.evidence : [];

  return {
    overall: measuredNumber(risk, "overall"),
    level: stringValue(risk, "level") || null,
    market: measuredNumber(risk, "market"),
    concentration: measuredNumber(risk, "concentration"),
    liquidity: measuredNumber(risk, "liquidity"),
    drawdown: measuredNumber(risk, "drawdown"),
    factors: stringList(risk, "factors"),
    evidence: evidence.flatMap((item) =>
      isRecord(item) && typeof item.statement === "string"
        ? [
            {
              statement: item.statement,
              source:
                typeof item.source === "string" ? item.source : "",
            },
          ]
        : [],
    ),
    unmeasured: stringList(risk, "unmeasured"),
  };
}

function capacityValue(payload: UnknownRecord): PortfolioCapacity | null {
  const capacity = payload.capacity;

  if (!isRecord(capacity)) {
    return null;
  }

  return {
    cashActualPct: numberValue(capacity, "cash_actual_pct"),
    cashTargetPct: measuredNumber(capacity, "cash_target_pct"),
    fundingRoomPct: measuredNumber(capacity, "funding_room_pct"),
    fundingRoomUsd: measuredNumber(capacity, "funding_room_usd"),
    singlePositionLimitPct: measuredNumber(capacity, "single_position_limit_pct"),
    largestPosition: stringValue(capacity, "largest_position") || null,
    largestPositionPct: measuredNumber(capacity, "largest_position_pct"),
    singlePositionHeadroomPct: measuredNumber(
      capacity,
      "single_position_headroom_pct",
    ),
    cryptoLimitPct: measuredNumber(capacity, "crypto_limit_pct"),
    cryptoActualPct: measuredNumber(capacity, "crypto_actual_pct"),
    cryptoHeadroomPct: measuredNumber(capacity, "crypto_headroom_pct"),
    unmeasured: stringList(capacity, "unmeasured"),
  };
}

function holdingsValue(portfolio: UnknownRecord): PortfolioHolding[] {
  const holdings = portfolio.holdings;

  if (!Array.isArray(holdings)) {
    return [];
  }

  return holdings.flatMap((item) => {
    if (!isRecord(item) || typeof item.symbol !== "string") {
      return [];
    }

    return [
      {
        symbol: item.symbol,
        resolved: item.resolved === true,
        assetClass: stringValue(item, "asset_class") || null,
        investedUsd: numberValue(item, "invested_usd"),
        marketValueUsd: numberValue(item, "market_value_usd"),
        unrealizedPnlUsd: numberValue(item, "unrealized_pnl_usd"),
        weightPct: measuredNumber(item, "weight_pct"),
      },
    ];
  });
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
        risk: riskValue(payload),
        capacity: capacityValue(payload),
        holdings: holdingsValue(portfolio),
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
