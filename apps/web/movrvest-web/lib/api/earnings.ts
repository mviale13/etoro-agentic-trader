const BACKEND_URL =
  process.env.MOVRVEST_API_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:8000";

/**
 * The book's own earnings calendar, exactly as the backend states it.
 *
 * The page renders these values and adds no meaning of its own: the
 * dates, the days-until arithmetic and the two absences all arrive
 * computed. "Unscheduled" and "unread" stay separate fields because
 * they are different facts — no published date is not a failed read.
 */
export interface EarningsEntry {
  symbol: string;
  name: string;
  startsOn: string;
  endsOn: string | null;
  startsInDays: number;
  held: boolean;
  observed: string;
}

export interface EarningsCalendar {
  upcoming: EarningsEntry[];
  reported: EarningsEntry[];
  unscheduled: string[];
  unread: string[];
}

export interface EarningsResult {
  calendar: EarningsCalendar | null;
  error: string | null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function strings(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((entry): entry is string => typeof entry === "string");
}

function entries(value: unknown): EarningsEntry[] {
  if (!Array.isArray(value)) {
    return [];
  }

  const parsed: EarningsEntry[] = [];

  for (const raw of value) {
    if (!isRecord(raw)) {
      continue;
    }

    if (
      typeof raw.symbol !== "string" ||
      typeof raw.starts_on !== "string" ||
      typeof raw.starts_in_days !== "number"
    ) {
      continue;
    }

    parsed.push({
      symbol: raw.symbol,
      name: typeof raw.name === "string" ? raw.name : raw.symbol,
      startsOn: raw.starts_on,
      endsOn: typeof raw.ends_on === "string" ? raw.ends_on : null,
      startsInDays: raw.starts_in_days,
      held: raw.held === true,
      observed: typeof raw.observed === "string" ? raw.observed : "",
    });
  }

  return parsed;
}

export async function getEarnings(): Promise<EarningsResult> {
  const endpoint = `${BACKEND_URL}/market/earnings`;

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
      throw new Error("The /market/earnings response is not a JSON object.");
    }

    return {
      calendar: {
        upcoming: entries(payload.upcoming),
        reported: entries(payload.reported),
        unscheduled: strings(payload.unscheduled),
        unread: strings(payload.unread),
      },
      error: null,
    };
  } catch (error) {
    return {
      calendar: null,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}
