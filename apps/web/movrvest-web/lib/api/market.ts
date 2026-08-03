const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

/**
 * How one corner of the market moved.
 *
 * "unknown" is a real answer and is rendered as one. A group nothing
 * could price did not fail to move — nobody looked at it, and showing it
 * as flat would put a reading on the page that was never taken.
 */
export type Direction =
  | "positive"
  | "neutral"
  | "negative"
  | "low"
  | "medium"
  | "high"
  | "unknown";

export interface MarketBreadth {
  equities: Direction;
  technology: Direction;
  smallCaps: Direction;
  crypto: Direction;
  commodities: Direction;
  volatility: Direction;
  dollar: Direction;
  rates: Direction;
}

export interface MarketQuote {
  symbol: string;
  name: string;
  price: number;
  changePercent: number;
  realizedVolatility: number | null;
  maxDrawdown: number | null;
}

/**
 * A published sentiment reading, and the asset class it describes.
 *
 * `subject` is rendered, always. The only index MOVRvest reads is a
 * crypto one, and a card labelled "market sentiment" invites the reader
 * to apply it to everything they hold.
 */
export interface MarketSentiment {
  score: number;
  label: string;
  subject: string;
  observed: string;
}

export interface MarketOverview {
  mood: string;
  summary: string;
  volatility: string;
  vix: number | null;
  observed: string | null;
  sentiment: MarketSentiment | null;
  breadth: MarketBreadth;
  quotes: MarketQuote[];
}

export interface MarketResult {
  market: MarketOverview | null;
  backendUrl: string;
  error?: string;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function direction(value: unknown): Direction {
  const allowed: Direction[] = [
    "positive",
    "neutral",
    "negative",
    "low",
    "medium",
    "high",
    "unknown",
  ];

  return allowed.includes(value as Direction) ? (value as Direction) : "unknown";
}

function numberOrNull(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function quotes(value: unknown): MarketQuote[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (!isRecord(item)) {
      return [];
    }

    const price = numberOrNull(item.price);

    if (typeof item.symbol !== "string" || price === null) {
      return [];
    }

    return [
      {
        symbol: item.symbol,
        name: typeof item.name === "string" ? item.name : item.symbol,
        price,
        changePercent: numberOrNull(item.change_percent) ?? 0,
        realizedVolatility: numberOrNull(item.realized_volatility),
        maxDrawdown: numberOrNull(item.max_drawdown),
      },
    ];
  });
}

function sentiment(value: unknown): MarketSentiment | null {
  if (!isRecord(value)) {
    return null;
  }

  const score = numberOrNull(value.score);

  // A reading with no score, label or subject is not a reading. Rendering
  // a partial one would put a mood on the page with nothing behind it.
  if (
    score === null ||
    typeof value.label !== "string" ||
    typeof value.subject !== "string"
  ) {
    return null;
  }

  return {
    score,
    label: value.label,
    subject: value.subject,
    observed: typeof value.observed === "string" ? value.observed : "",
  };
}

export async function getMarket(): Promise<MarketResult> {
  const endpoint = `${BACKEND_URL}/market/`;

  try {
    const response = await fetch(endpoint, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      const body = await response.text();

      throw new Error(
        `Backend returned ${response.status}: ${body.slice(0, 300)}`,
      );
    }

    const payload: unknown = await response.json();

    if (!isRecord(payload)) {
      throw new Error("The /market response is not a JSON object.");
    }

    const breadth = isRecord(payload.breadth) ? payload.breadth : {};

    return {
      market: {
        mood: typeof payload.mood === "string" ? payload.mood : "unknown",
        summary: typeof payload.summary === "string" ? payload.summary : "",
        volatility:
          typeof payload.volatility === "string" ? payload.volatility : "unknown",
        vix: numberOrNull(payload.vix),
        observed: typeof payload.observed === "string" ? payload.observed : null,
        sentiment: sentiment(payload.sentiment),
        breadth: {
          equities: direction(breadth.equities),
          technology: direction(breadth.technology),
          smallCaps: direction(breadth.small_caps),
          crypto: direction(breadth.crypto),
          commodities: direction(breadth.commodities),
          volatility: direction(breadth.volatility),
          dollar: direction(breadth.dollar),
          rates: direction(breadth.rates),
        },
        quotes: quotes(payload.quotes),
      },
      backendUrl: endpoint,
    };
  } catch (error) {
    return {
      market: null,
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
