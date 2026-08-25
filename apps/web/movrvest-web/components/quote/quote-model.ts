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
export function parseQuote(raw: unknown): FreshQuoteView | null {
  if (typeof raw !== "object" || raw === null) {
    return null;
  }

  const record = raw as Record<string, unknown>;

  const requireString = (key: string): string | null =>
    typeof record[key] === "string" ? (record[key] as string) : null;
  const optionalString = (key: string): string | null =>
    typeof record[key] === "string" ? (record[key] as string) : null;
  const optionalNumber = (key: string): number | null =>
    typeof record[key] === "number" && Number.isFinite(record[key] as number)
      ? (record[key] as number)
      : null;

  const symbol = requireString("movrvest_symbol");
  const status = requireString("status");
  const stated = requireString("stated");

  if (!symbol || !status || !stated) {
    return null;
  }

  return {
    movrvestSymbol: symbol,
    assetClass: requireString("asset_class") ?? "security",
    provider: requireString("provider") ?? "",
    providerInstrumentIdentity: optionalString("provider_instrument_identity"),
    providerLabel: optionalString("provider_label"),
    price: optionalNumber("price"),
    currency: optionalString("currency"),
    bid: optionalNumber("bid"),
    ask: optionalNumber("ask"),
    sourceAsOf: optionalString("source_as_of"),
    receivedAt: optionalString("received_at"),
    clockKind: requireString("clock_kind") ?? "receipt_only",
    delayStatus: requireString("delay_status") ?? "unknown",
    marketStatus: requireString("market_status") ?? "unknown",
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

/** "18 seconds ago" / "3 minutes ago" — from the source clock to the
    render moment, coarse on purpose: a ribbon is not a stopwatch. */
export function statedAge(iso: string, now: Date): string | null {
  const at = new Date(iso);

  if (Number.isNaN(at.getTime())) {
    return null;
  }

  const seconds = Math.max(0, Math.floor((now.getTime() - at.getTime()) / 1000));

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

  if (quote.status === "current" && quote.sourceAsOf) {
    const age = statedAge(quote.sourceAsOf, now);

    return {
      figure: formattedPrice(quote.price, quote.currency),
      attribution: age
        ? `Updated ${age} · ${quote.provider}`
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
