/**
 * The Overview's selectors — pure functions over the typed dossier.
 *
 * Everything the investor-facing Overview shows is chosen here, from
 * already-typed, already-curated evidence, so the rules the redesign
 * rests on are testable without rendering React:
 *
 * - nothing is parsed out of prose and nothing is invented — a summary
 *   whose carrier is absent yields an absent widget, never a shell;
 * - no ranking model: drivers, watch items and developments are taken
 *   in the order the backend curated them, capped at three;
 * - a conflict stays a conflict — a conflicted fact never serves a
 *   number, and no side of a source disagreement is chosen;
 * - raw fact identifiers (`network.fees.hyperliquid-protocol`,
 *   journal keys, refs) never reach the investor view;
 * - facts that do not exist are omitted — absence is not a card.
 */

import type {
  CryptoDossier,
  DriverView,
  EventView,
  FactRowView,
  MarketObservationView,
  ProtocolFactView,
  WatchItemView,
} from "@/lib/api/crypto-dossier";

// ── tabs ────────────────────────────────────────────────────────────

export const VIEWS = [
  "overview",
  "economics",
  "tokenomics",
  "developments",
  "evidence",
] as const;

export type CryptoView = (typeof VIEWS)[number];

export const VIEW_LABELS: Record<CryptoView, string> = {
  overview: "Overview",
  economics: "Economics",
  tokenomics: "Tokenomics",
  developments: "Developments",
  evidence: "Evidence",
};

/** The active view from the URL. Anything unrecognised is the default. */
export function viewFromParam(param: string | string[] | undefined): CryptoView {
  const value = Array.isArray(param) ? param[0] : param;

  return (VIEWS as readonly string[]).includes(value ?? "")
    ? (value as CryptoView)
    : "overview";
}

// ── hero ────────────────────────────────────────────────────────────

export interface HeroReturn {
  short: string;
  stated: string;
  standingStated: string;
}

export interface HeroModel {
  symbol: string;
  /** The recognised project name, where the corpus carries one. */
  name: string | null;
  /** The plain economic role — the playbook's own name. The fuller
      explanation stays under Evidence: its wording speaks in lenses
      and compositions, which the Overview deliberately does not. */
  role: string;
  /** The spot price row, exactly as the judged-facts gate served it. */
  price: FactRowView | null;
  returns: readonly HeroReturn[];
  state: string;
  /**
   * The one concise course line. Licensed by the decision's own
   * ceiling: while the ceiling stands, no digital asset carries a
   * capital action, and the spec asks for that said directly.
   */
  courseLine: string | null;
}

const RETURN_INTERVALS: Record<string, string> = {
  "24h": "24h",
  "7d": "7d",
  "30d": "30d",
};

function marketRow(
  dossier: CryptoDossier,
  label: string,
): FactRowView | null {
  for (const group of dossier.facts?.groups ?? []) {
    for (const row of group.rows) {
      if (row.label === label) {
        return row;
      }
    }
  }

  return null;
}

export function heroModel(
  dossier: CryptoDossier,
  name: string | null,
): HeroModel {
  const returns: HeroReturn[] = [];

  for (const item of dossier.market?.returns ?? []) {
    const short = RETURN_INTERVALS[item.interval];

    if (short && item.label === "Price return" && item.stated !== null) {
      returns.push({
        short,
        stated: item.stated,
        standingStated: item.standingStated,
      });
    }
  }

  return {
    symbol: dossier.symbol,
    name,
    role: dossier.identity.name,
    price: marketRow(dossier, "Price"),
    returns,
    state: dossier.decision.state,
    courseLine: dossier.decision.ceiling
      ? "No capital action is suggested."
      : null,
  };
}

// ── the three summary widgets ───────────────────────────────────────

const SUMMARY_LIMIT = 3;

export interface SummaryItem {
  stated: string;
  tag: string | null;
}

/** Supportive and context drivers, in the backend's own curated order. */
export function whyItMatters(dossier: CryptoDossier): readonly SummaryItem[] {
  const drivers = dossier.intelligence?.drivers ?? [];

  return drivers
    .filter((driver: DriverView) => driver.directionStated !== "Adverse")
    .slice(0, SUMMARY_LIMIT)
    .map((driver) => ({
      stated: driver.stated,
      tag: driver.directionStated,
    }));
}

/**
 * Adverse developments first, then the decision's own material
 * uncertainties — both already typed and already curated. Order within
 * each list is the backend's; nothing here ranks.
 */
export function keyRisks(dossier: CryptoDossier): readonly SummaryItem[] {
  const adverse = (dossier.intelligence?.drivers ?? [])
    .filter((driver: DriverView) => driver.directionStated === "Adverse")
    .map((driver) => ({ stated: driver.stated, tag: "Adverse development" }));

  const uncertainties = dossier.decision.materialUncertainties.map(
    (stated) => ({ stated, tag: "Material uncertainty" }),
  );

  return [...adverse, ...uncertainties].slice(0, SUMMARY_LIMIT);
}

export interface WatchItem {
  stated: string;
  measuredBy: string;
}

/** What to watch, without the refs — identifiers stay in Evidence. */
export function watchNext(dossier: CryptoDossier): readonly WatchItem[] {
  return (dossier.intelligence?.watchNext ?? [])
    .slice(0, SUMMARY_LIMIT)
    .map((item: WatchItemView) => ({
      stated: item.stated,
      measuredBy: item.measuredBy,
    }));
}

// ── key facts ───────────────────────────────────────────────────────

export interface KeyFact {
  label: string;
  /** Null exactly where the standing is a conflict — never a number. */
  stated: string | null;
  standing: string;
  standingStated: string;
  /** The short source/age line, where one exists. */
  age: string | null;
  /** Why it stands as it does — the honest range lives here for a
      conflict, in the backend's own sentence. */
  because: string | null;
  /** The economic entity a protocol figure belongs to. Null for
      market and supply facts, which have no entity. */
  entity: string | null;
}

/** Which judged-fact labels the compact widget shows, in this order.
    Price is deliberately absent: the hero owns it, and no fact may
    appear in two default widgets. */
const FACT_LABELS = [
  "Market value",
  "Market-value rank",
  "Reported market volume over 24 hours",
  "Maximum supply",
  "Circulating supply",
  "Total supply",
  "Fully diluted valuation",
] as const;

/** Which protocol-fact families the widget admits. */
const PROTOCOL_FAMILIES = new Set([
  "capital",
  "value_generation",
  "holder_accrual",
  "activity",
]);

function fromFactRow(row: FactRowView): KeyFact {
  return {
    label: row.label,
    stated: row.standing === "conflicted" ? null : row.stated,
    standing: row.standing,
    standingStated: row.standingStated,
    age: row.age,
    because: row.standing === "conflicted" ? row.because : null,
    entity: null,
  };
}

function fromProtocolFact(entity: string, fact: ProtocolFactView): KeyFact {
  return {
    label: fact.label,
    stated: fact.stated,
    standing: fact.standing,
    standingStated: fact.standingStated,
    age: fact.age,
    because: null,
    entity,
  };
}

/**
 * The compact facts that exist for this asset — and only those.
 *
 * An absent fact is omitted rather than rendered as an empty card; a
 * conflicted fact is kept, with no value and the backend's own account
 * of the disagreement; a zero is a value and stays. Nothing is
 * recomputed from other figures: every row is the judged fact that
 * already owns the value.
 */
export function keyFacts(dossier: CryptoDossier): readonly KeyFact[] {
  const rows: KeyFact[] = [];

  const byLabel = new Map<string, FactRowView>();

  for (const group of dossier.facts?.groups ?? []) {
    for (const row of group.rows) {
      byLabel.set(row.label, row);
    }
  }

  for (const label of FACT_LABELS) {
    const row = byLabel.get(label);

    if (row && row.standing !== "absent") {
      rows.push(fromFactRow(row));
    }
  }

  for (const entity of dossier.protocol?.entities ?? []) {
    for (const fact of entity.facts) {
      if (PROTOCOL_FAMILIES.has(fact.family) && fact.stated !== null) {
        rows.push(fromProtocolFact(entity.name, fact));
      }
    }
  }

  return rows;
}

// ── latest developments ─────────────────────────────────────────────

const DEVELOPMENTS_LIMIT = 3;

export interface Development {
  headline: string;
  /** The event family, worded for a reader. */
  category: string;
  age: string | null;
  /** One short relevance sentence — the first typed account held. */
  relevance: string | null;
  /** The verification standing, from the event's own source count. */
  verification: string;
  sources: readonly string[];
  accounts: readonly { stated: string; source: string }[];
}

function categoryLabel(family: string): string {
  const label = family.replace(/_/g, " ");

  return label.charAt(0).toUpperCase() + label.slice(1);
}

export function latestDevelopments(
  dossier: CryptoDossier,
): readonly Development[] {
  return (dossier.intelligence?.events ?? [])
    .slice(0, DEVELOPMENTS_LIMIT)
    .map((event: EventView) => ({
      headline: event.headline,
      category: categoryLabel(event.family),
      age: event.age ? event.age.replace(/^,\s*/, "") : null,
      relevance:
        event.interpretations[0]?.stated ?? event.facts[0]?.stated ?? null,
      verification: event.isMultiSource
        ? `Reported by ${event.sources.length} sources`
        : "Single source",
      sources: event.sources,
      accounts: event.interpretations.map((item) => ({
        stated: item.stated,
        source: item.source,
      })),
    }));
}

// ── decision block ──────────────────────────────────────────────────

export interface DecisionModel {
  state: string;
  rationale: string;
  /** What is unresolved — and therefore what could change this view. */
  unresolved: readonly { owner: string; stated: string }[];
  /** The platform boundary, disclosed once. */
  boundary: string | null;
  courseLine: string | null;
}

export function decisionModel(dossier: CryptoDossier): DecisionModel {
  return {
    state: dossier.decision.state,
    rationale: dossier.decision.rationale,
    unresolved: dossier.decision.unresolved,
    boundary: dossier.decision.ceiling || null,
    courseLine: dossier.decision.ceiling
      ? "No capital action is suggested."
      : null,
  };
}

// ── returns for the market observation type ─────────────────────────

export type { MarketObservationView };
