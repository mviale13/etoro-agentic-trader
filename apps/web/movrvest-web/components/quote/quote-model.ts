/**
 * The Fresh Quote Ribbon's wording rules — pure functions, no React.
 *
 * The ribbon may only ever say what the typed quote establishes:
 *
 * - **"Updated Ns ago" is the source's clock, never ours.** It renders
 *   only for a CURRENT quote, whose `clock_kind` is SOURCE_STATED by
 *   construction.
 * - **a stale quote says "as of <time>"** — the honest form of the same
 *   fact — and is never styled or worded as live. The words "live" and
 *   "real-time" appear nowhere in this module's vocabulary.
 * - **delay and market-closed sentences render only where a provider
 *   stated them.** The measured provider states neither, so with
 *   today's data they never render — the branches exist for a provider
 *   that does, not as inferences.
 * - **the fallback is the established price, named as what it is.** A
 *   crypto hero with no current quote shows "Last established price"
 *   with its actual age, or "Price unavailable." — never a stale value
 *   dressed as fresh.
 */

export interface FreshQuoteView {
  movrvestSymbol: string;
  assetClass: string;
  provider: string;
  providerInstrumentIdentity: string | null;
  providerLabel: string | null;
  price: number | null;
  currency: string | null;
  bid: number | null;
  ask: number | null;
  sourceAsOf: string | null;
  receivedAt: string | null;
  clockKind: string;
  delayStatus: string;
  marketStatus: string;
  status: string;
  stated: string;
}

/** The wire shape, validated strictly: a malformed quote is no quote. */
const ASSET_CLASSES = new Set(["security", "crypto"]);
const CLOCK_KINDS = new Set(["source_stated", "receipt_only"]);
const DELAY_STATUSES = new Set(["real_time", "delayed", "unknown"]);
const MARKET_STATUSES = new Set(["open", "closed", "unknown"]);
const STATUSES = new Set(["current", "stale", "identity_refused", "unavailable"]);

/**
 * Genuinely fail-closed: every wire field must exist with its declared
 * shape, every enum is checked by membership, and nothing is defaulted.
 *
 * The earlier version claimed this and defaulted five fields — a
 * missing `clock_kind` became `receipt_only`, a missing `asset_class`
 * became `security` — which meant a truncated `current` response could
 * parse into a plausible current quote. Now a malformed answer is no
 * answer: a `current` quote missing its clock kind, source moment,
 * identity, provider or price does not exist here.
 *
 * A displayed price must be finite and strictly positive; anything else
 * fails the parse rather than rendering as a figure. Invalid bid/ask
 * merely become null — they qualify a price, they are not the price.
 */
export function parseQuote(raw: unknown): FreshQuoteView | null {
  if (typeof raw !== "object" || raw === null) {
    return null;
  }

  const record = raw as Record<string, unknown>;

  const requiredString = (key: string): string | null =>
    typeof record[key] === "string" && (record[key] as string) !== ""
      ? (record[key] as string)
      : null;

  // Present, and either a string or an explicit null — an absent key is
  // a malformed message, not an absent value.
  const nullableString = (key: string): string | null | undefined => {
    if (!(key in record)) {
      return undefined;
    }

    const value = record[key];

    return value === null || typeof value === "string"
      ? (value as string | null)
      : undefined;
  };

  const nullableNumber = (key: string): number | null | undefined => {
    if (!(key in record)) {
      return undefined;
    }

    const value = record[key];

    if (value === null) {
      return null;
    }

    return typeof value === "number" && Number.isFinite(value)
      ? value
      : undefined;
  };

  const enumMember = (key: string, allowed: Set<string>): string | null => {
    const value = record[key];

    return typeof value === "string" && allowed.has(value) ? value : null;
  };

  const symbol = requiredString("movrvest_symbol");
  const assetClass = enumMember("asset_class", ASSET_CLASSES);
  const provider = requiredString("provider");
  const status = enumMember("status", STATUSES);
  const clockKind = enumMember("clock_kind", CLOCK_KINDS);
  const delayStatus = enumMember("delay_status", DELAY_STATUSES);
  const marketStatus = enumMember("market_status", MARKET_STATUSES);
  const stated = requiredString("stated");

  const identity = nullableString("provider_instrument_identity");
  const label = nullableString("provider_label");
  const price = nullableNumber("price");
  const currency = nullableString("currency");
  const sourceAsOf = nullableString("source_as_of");
  const receivedAt = nullableString("received_at");

  if (
    !symbol ||
    !assetClass ||
    !provider ||
    !status ||
    !clockKind ||
    !delayStatus ||
    !marketStatus ||
    !stated ||
    identity === undefined ||
    label === undefined ||
    price === undefined ||
    currency === undefined ||
    sourceAsOf === undefined ||
    receivedAt === undefined
  ) {
    return null;
  }

  // A headline price is finite and strictly positive, or the whole
  // answer is refused — a zero or negative figure rendered large is
  // worse than no figure.
  if (price !== null && price <= 0) {
    return null;
  }

  // A current quote is a compound claim: it needs the source's own
  // clock, that clock's moment, the instrument's identity and a price.
  // Missing any of them, "current" is not a state this parser can
  // hand to a renderer.
  if (
    status === "current" &&
    (clockKind !== "source_stated" ||
      sourceAsOf === null ||
      identity === null ||
      price === null)
  ) {
    return null;
  }

  // Invalid bid/ask become null rather than failing the quote: they
  // qualify the price, they are not the price.
  const bid = nullableNumber("bid");
  const ask = nullableNumber("ask");

  return {
    movrvestSymbol: symbol,
    assetClass,
    provider,
    providerInstrumentIdentity: identity,
    providerLabel: label,
    price,
    currency,
    bid: bid === undefined || (bid !== null && bid <= 0) ? null : bid,
    ask: ask === undefined || (ask !== null && ask <= 0) ? null : ask,
    sourceAsOf,
    receivedAt,
    clockKind,
    delayStatus,
    marketStatus,
    status,
    stated,
  };
}

// ── presentation ────────────────────────────────────────────────────

export interface RibbonModel {
  /** The formatted figure. The measured provider names no currency, so
      no symbol is invented; a provider that names one gets it printed. */
  figure: string;
  /** The one line under the figure: freshness or the honest "as of". */
  attribution: string;
  /** Provider-stated conditions only; empty with today's provider. */
  qualifiers: readonly string[];
  /** True only for a CURRENT quote — the caller may use it to decide
      placement, never to add wording of its own. */
  current: boolean;
}

function formattedPrice(price: number, currency: string | null): string {
  const figure = price.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: price < 10 ? 4 : 2,
  });

  return currency ? `${currency} ${figure}` : figure;
}

/** How old a source-stated quote may be at render time and still be
    presented as current. The same 120-second window the backend uses at
    receipt, applied again here because the browser keeps rendering long
    after the backend last answered. */
export const CURRENT_WINDOW_SECONDS = 120;

/** The quote's age at the render moment, in seconds, on the source's
    own clock — or null where no valid source moment exists. Negative
    for a source clock ahead of the render clock, and deliberately not
    clamped: a future moment is a refused claim, not a zero-second-old
    one. */
export function sourceAgeSeconds(
  sourceAsOf: string | null,
  now: Date,
): number | null {
  if (!sourceAsOf) {
    return null;
  }

  const at = new Date(sourceAsOf);

  if (Number.isNaN(at.getTime())) {
    return null;
  }

  return (now.getTime() - at.getTime()) / 1000;
}

/** "18 seconds ago" / "3 minutes ago" — from the source clock to the
    render moment, coarse on purpose: a ribbon is not a stopwatch. A
    negative age is refused, never clamped to zero. */
export function statedAge(iso: string, now: Date): string | null {
  const age = sourceAgeSeconds(iso, now);

  if (age === null || age < 0) {
    return null;
  }

  const seconds = Math.floor(age);

  if (seconds < 60) {
    return `${seconds} second${seconds === 1 ? "" : "s"} ago`;
  }

  const minutes = Math.floor(seconds / 60);

  if (minutes < 60) {
    return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  }

  const hours = Math.floor(minutes / 60);

  return `${hours} hour${hours === 1 ? "" : "s"} ago`;
}

function statedInstant(iso: string): string | null {
  const at = new Date(iso);

  if (Number.isNaN(at.getTime())) {
    return null;
  }

  const hours = at.getUTCHours().toString().padStart(2, "0");
  const minutes = at.getUTCMinutes().toString().padStart(2, "0");

  return `${hours}:${minutes} UTC`;
}

/**
 * What the ribbon may render for one quote, or null where it renders
 * nothing at all.
 *
 * Null for IDENTITY_REFUSED and UNAVAILABLE, and for any quote with no
 * price: the callers own their fallbacks (the crypto hero falls back to
 * the established price; the stock hero simply shows no ribbon, which
 * is what it showed before this existed).
 */
export function ribbonModel(
  quote: FreshQuoteView | null,
  now: Date,
): RibbonModel | null {
  if (!quote || quote.price === null) {
    return null;
  }

  if (quote.status !== "current" && quote.status !== "stale") {
    return null;
  }

  const qualifiers: string[] = [];

  // Provider-stated conditions only. The measured provider states
  // neither, so both branches are dead with today's data — that is the
  // point: they can only come alive when a provider speaks.
  if (quote.delayStatus === "delayed") {
    qualifiers.push("Quote delayed");
  }

  if (quote.marketStatus === "closed") {
    qualifiers.push("Market closed");
  }

  // **Currency expires in the browser.** The backend judged `current`
  // at receipt, but this page keeps rendering long after that answer —
  // a network failure after one success would otherwise leave "Updated
  // 0 seconds ago" standing forever. So the presentation re-asks the
  // whole compound claim at render time: the current status, the
  // source's own clock, a valid source moment, and an age between zero
  // and the window on that clock right now. A future source moment
  // fails the same gate — a claim about the future establishes nothing
  // about the present.
  const age = sourceAgeSeconds(quote.sourceAsOf, now);

  const currentAtRender =
    quote.status === "current" &&
    quote.clockKind === "source_stated" &&
    age !== null &&
    age >= 0 &&
    age <= CURRENT_WINDOW_SECONDS;

  if (currentAtRender && quote.sourceAsOf) {
    const stated = statedAge(quote.sourceAsOf, now);

    return {
      figure: formattedPrice(quote.price, quote.currency),
      attribution: stated
        ? `Updated ${stated} · ${quote.provider}`
        : `As of ${statedInstant(quote.sourceAsOf) ?? quote.sourceAsOf} · ${quote.provider}`,
      qualifiers,
      current: true,
    };
  }

  // Stale: the price with its honest clock. Where even the source
  // moment is unknown (a receipt-only quote), the age of the *receipt*
  // is never shown as the age of the observation — the attribution
  // falls back to the quote's own stated sentence.
  const asOf = quote.sourceAsOf ? statedInstant(quote.sourceAsOf) : null;

  return {
    figure: formattedPrice(quote.price, quote.currency),
    attribution: asOf
      ? `As of ${asOf} · ${quote.provider}`
      : quote.stated,
    qualifiers,
    current: false,
  };
}

// ── the crypto fallback ─────────────────────────────────────────────

export interface HeadlineModel {
  kind: "fresh" | "established" | "absent";
  ribbon: RibbonModel | null;
  /** For the established fallback: the stored figure and its own age
      sentence, exactly as the judged-facts gate served them. */
  establishedStated: string | null;
  establishedAge: string | null;
}

/**
 * Which price leads a crypto hero.
 *
 * A CURRENT fresh quote is the headline. Anything less falls back to
 * the stored established price labelled as what it is — "Last
 * established price", with its actual age — and where none is held the
 * state is stated. A stale fresh quote never outranks the established
 * figure here: "current or fallback" is the rule, with no middle tier
 * that could dress a stale value as fresh.
 */
export function headlineModel(
  quote: FreshQuoteView | null,
  established: { stated: string | null; age: string | null } | null,
  now: Date,
): HeadlineModel {
  const ribbon = ribbonModel(quote, now);

  if (ribbon && ribbon.current) {
    return {
      kind: "fresh",
      ribbon,
      establishedStated: null,
      establishedAge: null,
    };
  }

  if (established?.stated) {
    return {
      kind: "established",
      ribbon: null,
      establishedStated: established.stated,
      establishedAge: established.age,
    };
  }

  return {
    kind: "absent",
    ribbon: null,
    establishedStated: null,
    establishedAge: null,
  };
}
