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

import type { RecordedPortfolio } from "@/lib/api/cycle-review";
import type {
  BriefView,
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

/**
 * What the investor already owns of this asset, from the last completed
 * cycle — never from a live account read.
 *
 * A dated share of a recorded portfolio, and the date travels with it.
 * `held: false` is a positive finding and not a missing value: the
 * cycle recorded fourteen holdings and this asset was not among them,
 * which is different from *we could not read your account*, and that
 * third state is `null` exposure altogether.
 */
export interface ExposureModel {
  held: boolean;
  weightStated: string | null;
  valueStated: string | null;
  /** The cycle's own receipt-time wording. Never reworded here. */
  observed: string;
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
   * What the course means for capital — the CIO layer's sentence, and
   * the **only** place it appears. It was previously rendered here and
   * again in the card below, so the investor read "INVESTIGATE — no
   * capital action is suggested" twice before reaching a finding.
   */
  courseLine: string | null;
  /**
   * One sentence: what is supportive, set against what is not
   * established. Composed by the CIO layer from quoted findings —
   * never worded here.
   */
  setup: string | null;
  /** Why no setup could be stated, where none could. */
  setupAbsent: string | null;
  /** Null where no completed cycle could be read at all. */
  exposure: ExposureModel | null;
}

/** The windows the hero leads with, and the short label each carries. */
const RETURN_INTERVALS: Record<string, string> = {
  "24h": "24h",
  "7d": "7d",
  "30d": "30d",
};

/**
 * Every window the market layer measures, including the 1h the hero
 * omits — and short labels, because the backend's own
 * ``intervalStated`` reads "over 30 days" and four of those wrapped the
 * setup row into three lines on a phone. The label is this surface's to
 * choose; the figure and the window it belongs to are not.
 */
const SETUP_INTERVALS: Record<string, string> = {
  "1h": "1h",
  ...RETURN_INTERVALS,
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

/**
 * This asset's place in the recorded portfolio, or the fact it has none.
 *
 * Reads the last completed cycle only. A cycle still running, or a
 * portfolio the record could not carry, yields `null` — the surface
 * then says nothing about exposure rather than implying zero.
 */
export function exposureModel(
  symbol: string,
  portfolio: RecordedPortfolio | null,
): ExposureModel | null {
  if (portfolio === null) {
    return null;
  }

  const holding = portfolio.holdings.find((item) => item.symbol === symbol);

  if (holding === undefined) {
    return { held: false, weightStated: null, valueStated: null, observed: portfolio.observed };
  }

  return {
    held: true,
    // `weight_pct` is null where the share could not be computed, and
    // the record is explicit that this is never 0.0 for it — so an
    // uncomputable share stays absent instead of reading as no position.
    weightStated:
      holding.weightPct === null ? null : `${holding.weightPct.toFixed(1)}%`,
    valueStated: CURRENCY.format(holding.marketValueUsd),
    observed: portfolio.observed,
  };
}

const CURRENCY = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export function heroModel(
  dossier: CryptoDossier,
  name: string | null,
  portfolio: RecordedPortfolio | null = null,
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
    state: dossier.brief.course,
    courseLine: dossier.brief.courseMeans || null,
    setup: dossier.brief.setup,
    setupAbsent: dossier.brief.setupAbsent,
    exposure: exposureModel(dossier.symbol, portfolio),
  };
}

// ── market setup ────────────────────────────────────────────────────

/**
 * Where the price is, and over what windows — nothing conditional.
 *
 * The brief asked for two more things and **neither is held**: a
 * position within the recent measured range, and volume against a
 * normal. There is no high, no low and no baseline anywhere in the
 * payload — the only "all-time" figures in the corpus are event
 * headlines about *open interest*, which is a different quantity — so
 * both are named as absences rather than approximated from returns.
 * Deriving a range from a 30-day return would be this surface
 * calculating, which it may not do.
 */
export interface MarketSetupModel {
  returns: readonly HeroReturn[];
  volumeStated: string | null;
  volumeAge: string | null;
  /** What this platform cannot yet say about the setup, and why. */
  unavailable: readonly string[];
}

export function marketSetup(dossier: CryptoDossier): MarketSetupModel {
  const returns: HeroReturn[] = [];

  for (const item of dossier.market?.returns ?? []) {
    const short = SETUP_INTERVALS[item.interval];

    if (short && item.label === "Price return" && item.stated !== null) {
      returns.push({
        short,
        stated: item.stated,
        standingStated: item.standingStated,
      });
    }
  }

  const volume = marketRow(dossier, "Reported market volume over 24 hours");

  return {
    returns,
    volumeStated: volume?.stated ?? null,
    volumeAge: volume?.age ?? null,
    unavailable: [
      "Where the price sits in its recent range is not stated: no high " +
        "or low is held for this asset over any window.",
      "Whether today's volume is normal is not stated: no baseline " +
        "volume is held to compare it against.",
    ],
  };
}

// ── the three summary widgets ───────────────────────────────────────

const SUMMARY_LIMIT = 3;

/**
 * One block of the CIO brief, ready to render.
 *
 * A pass-through with a heading attached. The lines, their order, their
 * count and their absences were all settled by the CIO layer — this
 * names the block and stops, so no ranking, filtering or re-wording can
 * enter on the way to the page.
 */
export interface BriefBlock {
  id: string;
  title: string;
  lines: readonly {
    stated: string;
    owner: string;
    qualification: string | null;
    support: string | null;
  }[];
  absent: string | null;
  /** How many findings this block holds back, where it holds any. */
  withheld: number;
}

export function briefBlocks(brief: BriefView): readonly BriefBlock[] {
  const withheld = new Map(brief.withheld.map((item) => [item.block, item.count]));

  return [
    {
      id: "current_view",
      title: "Current view",
      lines: brief.currentView,
      absent: brief.currentViewAbsent,
      withheld: withheld.get("current_view") ?? 0,
    },
    {
      id: "blocks_progress",
      title: "What blocks progress",
      lines: brief.blocksProgress,
      absent: brief.blocksProgressAbsent,
      withheld: withheld.get("blocks_progress") ?? 0,
    },
    {
      id: "would_change_view",
      title: "What would change the view",
      lines: brief.wouldChangeView,
      absent: brief.wouldChangeViewAbsent,
      withheld: withheld.get("would_change_view") ?? 0,
    },
  ];
}

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
 * The decision's own material uncertainties first, then adverse
 * developments in whatever room is left — both already typed and
 * already curated. Order within each list is the backend's.
 *
 * **This is not a risk-ranking model.** Nothing here scores, weighs or
 * reads sentiment; the only rule is whose authority comes first. The
 * decision owns the uncertainties that constrain the CIO's own view, so
 * they are never displaced by current news: with three adverse
 * developments and one material uncertainty, the earlier ordering
 * pushed the structural constraint off a three-item widget entirely and
 * the investor lost the very thing the course rests on.
 */
export function keyRisks(dossier: CryptoDossier): readonly SummaryItem[] {
  const uncertainties = dossier.decision.materialUncertainties.map(
    (stated) => ({ stated, tag: "Material uncertainty" }),
  );

  const adverse = (dossier.intelligence?.drivers ?? [])
    .filter((driver: DriverView) => driver.directionStated === "Adverse")
    .map((driver) => ({ stated: driver.stated, tag: "Adverse development" }));

  return [...uncertainties, ...adverse].slice(0, SUMMARY_LIMIT);
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

/**
 * How many metrics the Overview shows before sending the reader on.
 *
 * Six. The measured problem was that sixteen rows — two TVL readings,
 * four fee and revenue figures, DEX volume, open interest, four supply
 * values and two 400-character conflict essays — made a 1,362px block
 * that dominated the page and buried the developments beside it. The
 * rest is not deleted; it is where it belongs, under Economics and
 * Tokenomics, and the Overview links to both.
 */
export const KEY_FACT_LIMIT = 6;

/** Which judged-fact labels the compact widget shows, in this order.
    Price is deliberately absent: the hero owns it, and no fact may
    appear in two default widgets. */
const FACT_LABELS = [
  "Market value",
  "Reported market volume over 24 hours",
  "Fully diluted valuation",
  "Circulating supply",
  "Maximum supply",
  "Market-value rank",
] as const;

/**
 * Which protocol quantities the snapshot admits, in preference order.
 *
 * By **label**, not by family: the families carry four figures each
 * across two mapped entities, so admitting a family admitted eight rows
 * where the investor needed one. Fees, holder revenue and the second
 * entity's readings are the Economics view's subject.
 */
const PROTOCOL_LABELS = [
  "Total value locked",
  "Protocol revenue",
  "Open interest",
] as const;

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
  const market: KeyFact[] = [];
  const protocol: KeyFact[] = [];

  const byLabel = new Map<string, FactRowView>();

  for (const group of dossier.facts?.groups ?? []) {
    for (const row of group.rows) {
      byLabel.set(row.label, row);
    }
  }

  for (const label of FACT_LABELS) {
    const row = byLabel.get(label);

    if (row && row.standing !== "absent") {
      market.push(fromFactRow(row));
    }
  }

  // One row per quantity, from the first mapped entity that reports it.
  // Hyperliquid maps two entities and both publish a total value locked
  // ($6.73bn and $1.53bn); printing both put the investor in the middle
  // of an entity-mapping question the Overview does not ask, and the
  // Economics view does.
  const taken = new Set<string>();

  for (const label of PROTOCOL_LABELS) {
    for (const entity of dossier.protocol?.entities ?? []) {
      if (taken.has(label)) {
        break;
      }

      for (const fact of entity.facts) {
        if (fact.label === label && fact.stated !== null) {
          protocol.push(fromProtocolFact(entity.name, fact));
          taken.add(label);
          break;
        }
      }
    }
  }

  // Interleaved by kind rather than concatenated, so the six that
  // survive are never all of one kind: an asset with no mapped protocol
  // shows six market rows, and one with both shows three of each.
  const rows: KeyFact[] = [];

  for (let index = 0; rows.length < KEY_FACT_LIMIT; index += 1) {
    const next = [market[index], protocol[index]].filter(
      (row): row is KeyFact => row !== undefined,
    );

    if (next.length === 0) {
      break;
    }

    rows.push(...next.slice(0, KEY_FACT_LIMIT - rows.length));
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
  /**
   * How many surfaces reported this development — **coverage, never
   * verification.** Two outlets carrying one account are two reports of
   * it and not a check on it, and no typed carrier here establishes
   * that anything was verified, confirmed, corroborated or agreed. The
   * name says coverage so that a later reader cannot borrow a stronger
   * claim from the field it arrived in.
   */
  sourceCoverage: string;
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
      sourceCoverage: event.isMultiSource
        ? `Reported by ${event.sources.length} sources`
        : "One source",
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
