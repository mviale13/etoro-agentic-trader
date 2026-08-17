const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

/**
 * The backend contract, mirrored exactly.
 *
 * The page never guesses at field names: if the backend renames one the
 * parse fails loudly instead of quietly rendering a track record with
 * holes that read as results.
 */
export interface TrackRecordOutcome {
  symbol: string;
  state: string;
  /** Null where the decision carried none. The price move is measured
      regardless: what the security did does not depend on whether the
      platform put a number on the decision. */
  conviction: number | null;
  decidedOn: string;
  pricedOn: string;
  changePct: number;
  daysElapsed: number;
  /** Null where the decision implied nothing or the move was too small. */
  agreed: boolean | null;
  /** Worded by the backend: "as decided", "against the decision", "not a call". */
  verdict: string;
  reading: string;
}

export interface UnscoredReason {
  reason: string;
  count: number;
}

export interface TrackRecordViewModel {
  recorded: number;
  measured: number;
  calls: number;
  agreed: number;
  /** Null until enough calls exist for a rate to mean anything. */
  hitRate: number | null;
  minimumCalls: number;
  unscoredTotal: number;
  outcomes: readonly TrackRecordOutcome[];
  unscoredReasons: readonly UnscoredReason[];
}

export interface TrackRecordResult {
  record: TrackRecordViewModel | null;
  backendUrl: string;
  error?: string;
}

/** The verdicts the backend words; anything else fails the parse. */
const VERDICTS = ["as decided", "against the decision", "not a call"] as const;

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

function parseOutcome(payload: unknown, index: number): TrackRecordOutcome {
  if (!isRecord(payload)) {
    throw new Error(`outcomes[${index}] is not a JSON object.`);
  }

  const at = (field: string) => `outcomes[${index}].${field}`;

  const verdict = requireString(payload.verdict, at("verdict"));

  if (!VERDICTS.includes(verdict as (typeof VERDICTS)[number])) {
    // A verdict this page has no rendering for is a contract change,
    // not a value to display verbatim under old assumptions.
    throw new Error(`Unknown verdict "${verdict}" at ${at("verdict")}.`);
  }

  const agreed = payload.agreed;

  if (agreed !== null && typeof agreed !== "boolean") {
    throw new Error(`Expected boolean or null at ${at("agreed")}.`);
  }

  return {
    symbol: requireString(payload.symbol, at("symbol")),
    state: requireString(payload.state, at("state")),
    conviction:
      typeof payload.conviction === "number" &&
      Number.isFinite(payload.conviction)
        ? payload.conviction
        : null,
    decidedOn: requireString(payload.decided_on, at("decided_on")),
    pricedOn: requireString(payload.priced_on, at("priced_on")),
    changePct: requireNumber(payload.change_pct, at("change_pct")),
    daysElapsed: requireNumber(payload.days_elapsed, at("days_elapsed")),
    agreed,
    verdict,
    reading: requireString(payload.reading, at("reading")),
  };
}

function parseReason(payload: unknown, index: number): UnscoredReason {
  if (!isRecord(payload)) {
    throw new Error(`unscored_reasons[${index}] is not a JSON object.`);
  }

  return {
    reason: requireString(payload.reason, `unscored_reasons[${index}].reason`),
    count: requireNumber(payload.count, `unscored_reasons[${index}].count`),
  };
}

export async function getTrackRecord(): Promise<TrackRecordResult> {
  const endpoint = `${BACKEND_URL}/track-record/`;

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
      throw new Error("The /track-record response is not a JSON object.");
    }

    const outcomes = Array.isArray(payload.outcomes) ? payload.outcomes : [];
    const reasons = Array.isArray(payload.unscored_reasons)
      ? payload.unscored_reasons
      : [];

    const hitRate = payload.hit_rate;

    if (hitRate !== null && typeof hitRate !== "number") {
      throw new Error('Expected a number or null at "hit_rate".');
    }

    return {
      record: {
        recorded: requireNumber(payload.recorded, "recorded"),
        measured: requireNumber(payload.measured, "measured"),
        calls: requireNumber(payload.calls, "calls"),
        agreed: requireNumber(payload.agreed, "agreed"),
        hitRate,
        minimumCalls: requireNumber(payload.minimum_calls, "minimum_calls"),
        unscoredTotal: requireNumber(payload.unscored_total, "unscored_total"),
        outcomes: outcomes.map(parseOutcome),
        unscoredReasons: reasons.map(parseReason),
      },
      backendUrl: endpoint,
    };
  } catch (error) {
    // No demo record. An unreachable backend means the track record is
    // unknown, and a fabricated one would be worse than none: this is
    // the one page whose whole subject is whether the platform's claims
    // survive contact with prices.
    return {
      record: null,
      backendUrl: endpoint,
      error: error instanceof Error ? error.message : "Unknown backend error",
    };
  }
}
