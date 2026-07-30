const MOVRVEST_API_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ??
  "http://127.0.0.1:8000";

export type DataSource = "backend" | "unavailable";

export interface BrainPortfolio {
  totalValue: number;
  totalValueEur: number;
  positions: number;
  cashAllocation: number;
}

export interface BrainObservation {
  title: string;
  message: string;
}

export interface InvestorDna {
  confidence: number;
  message: string;
}

export interface BrainRecommendation {
  symbol: string;
  action: string;
  confidence: number;
}

export interface BrainSnapshot {
  summary: string;
  portfolio: BrainPortfolio;
  observation: BrainObservation;
  investorDna: InvestorDna;
  recommendation: BrainRecommendation;
}

export interface ApiResult<T> {
  data: T | null;
  source: DataSource;
  endpoint: string;
  error?: string;
}

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readRecord(
  record: UnknownRecord,
  key: string,
): UnknownRecord | undefined {
  const value = record[key];
  return isRecord(value) ? value : undefined;
}

function readString(
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

function readNumber(
  record: UnknownRecord,
  key: string,
  fallback = 0,
): number {
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

  return fallback;
}

async function getJson<T>(
  path: string,
  mapper: (payload: UnknownRecord) => T,
): Promise<ApiResult<T>> {
  const endpoint = `${MOVRVEST_API_URL}${path}`;

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
      throw new Error("Backend response is not a JSON object.");
    }

    return {
      data: mapper(payload),
      source: "backend",
      endpoint,
    };
  } catch (error) {
    return {
      data: null,
      source: "unavailable",
      endpoint,
      error:
        error instanceof Error
          ? error.message
          : "Unknown backend connection error.",
    };
  }
}

function mapBrainSnapshot(payload: UnknownRecord): BrainSnapshot {
  const portfolio = readRecord(payload, "portfolio") ?? {};
  const observation = readRecord(payload, "observation") ?? {};
  const investorDna = readRecord(payload, "investor_dna") ?? {};
  const recommendation = readRecord(payload, "recommendation") ?? {};

  return {
    summary: readString(
      payload,
      "summary",
      "No executive summary is currently available.",
    ),
    portfolio: {
      totalValue: readNumber(portfolio, "total_value"),
      totalValueEur: readNumber(portfolio, "total_value_eur"),
      positions: readNumber(portfolio, "positions"),
      cashAllocation: readNumber(portfolio, "cash_allocation"),
    },
    observation: {
      title: readString(
        observation,
        "title",
        "No current observation",
      ),
      message: readString(
        observation,
        "message",
        "MOVRvest has not recorded a portfolio observation yet.",
      ),
    },
    investorDna: {
      confidence: readNumber(investorDna, "confidence"),
      message: readString(
        investorDna,
        "message",
        "MOVRvest is still learning your investment style.",
      ),
    },
    recommendation: {
      symbol: readString(recommendation, "symbol", "—"),
      action: readString(recommendation, "action", "NO ACTION"),
      confidence: readNumber(recommendation, "confidence"),
    },
  };
}

export function getBrainSnapshot(): Promise<ApiResult<BrainSnapshot>> {
  return getJson("/brain/", mapBrainSnapshot);
}

export function getPortfolio(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/portfolio/", (payload) => payload);
}

export function getPortfolioHealth(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/portfolio-health/", (payload) => payload);
}

export function getInvestorDna(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/investor-dna/", (payload) => payload);
}

export function getStrategy(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/strategy/", (payload) => payload);
}

export function getStrategyReadiness(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/strategy/readiness", (payload) => payload);
}

export function getLatestRecommendation(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/recommendations/latest", (payload) => payload);
}

export function getRecommendationTimeline(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/recommendations/timeline", (payload) => payload);
}

export function getOpportunities(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/opportunities/", (payload) => payload);
}

export function getCommitteeMembers(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/committee/members", (payload) => payload);
}

export function getCommitteeStatistics(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/committee/statistics", (payload) => payload);
}

export function getCommitteeWeights(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/committee/weights", (payload) => payload);
}

export function getReflection(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/reflection/", (payload) => payload);
}

export function getToday(): Promise<ApiResult<UnknownRecord>> {
  return getJson("/api/today", (payload) => payload);
}
