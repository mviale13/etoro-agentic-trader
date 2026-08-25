/**
 * The stock dossier's Overview selectors — pure functions over the
 * typed dossier and the recorded cycle course.
 *
 * The same shape #252 proved on the crypto side: every rule the
 * redesign rests on is decided here, from already-typed evidence, so it
 * is testable without rendering React. What that buys is specific —
 *
 * - **the course travels from the action carrier and from nowhere
 *   else.** `RECOMMEND` is a disposition; *"Consider adding to DIS"* is
 *   an action, and the second is never manufactured from the first. A
 *   dossier with no action carrier says so and shows the disposition
 *   alone;
 * - **no ranking model.** Items are taken in the order the backend
 *   curated them, capped at three. The only rule is precedence of
 *   authorship: what the decision owns comes before what an analyst
 *   observed;
 * - **company facts, portfolio facts and market facts stay apart.**
 *   `contextStrengths`/`contextRisks` are about the account and the
 *   market and reach none of these widgets — an account-wide condition
 *   is not a reason to revisit a company;
 * - **nothing is parsed out of prose and no number is reinterpreted.**
 *   The envelope renders its own sentence; `finalPct` is never read;
 * - absence omits a widget rather than filling it with "not
 *   established" cards.
 */

import type {
  CycleCourse,
  CycleReview,
  RecordedHolding,
} from "@/lib/api/cycle-review";
import type { DossierViewModel } from "@/lib/api/dossier";

// ── views ───────────────────────────────────────────────────────────

export const VIEWS = [
  "overview",
  "financials",
  "thesis",
  "developments",
  "evidence",
] as const;

export type DossierView = (typeof VIEWS)[number];

export const VIEW_LABELS: Record<DossierView, string> = {
  overview: "Overview",
  financials: "Financials",
  thesis: "Thesis & history",
  developments: "Developments",
  evidence: "Evidence",
};

/** The active view from the URL. Anything unrecognised is the default. */
export function viewFromParam(
  param: string | string[] | undefined,
): DossierView {
  const value = Array.isArray(param) ? param[0] : param;

  return (VIEWS as readonly string[]).includes(value ?? "")
    ? (value as DossierView)
    : "overview";
}

// ── hero ────────────────────────────────────────────────────────────

/**
 * What the hero can honestly show.
 *
 * **There is no price field, no company-name field and no return
 * field, and that is a finding rather than an omission.** Stage 0
 * traced all three:
 *
 * - `CompanyFacts` carries `name`, `current_price`, `price_identity`,
 *   `price_reading` and `daily_change_pct` — and `CompanyFacts` is
 *   imported nowhere in `app/brain/`. The dossier route holds a
 *   `CompanyRecommendation`, which has none of them;
 * - `InvestmentCase.company_name` is declared and assigned nowhere in
 *   the codebase;
 * - no API response model exposes an equity name, price or return, and
 *   no frontend surface renders one.
 *
 * So the hero shows the ticker alone, as the specification directs when
 * no typed carrier exists. Declaring the fields and filling them with
 * `null` would be a shell; reading a name out of a provider string
 * would be worse. A DIS news headline contains the words "Walt Disney"
 * — that is article text with no identity authority behind it, and it
 * is not a name carrier.
 */
export interface HeroModel {
  symbol: string;
  /** The provider's industry line, dated, with its own sentence. */
  industry: {
    label: string;
    sector: string | null;
    stated: string;
    age: string | null;
  } | null;
  /** When the latest completed CIO review finished. Null where the
      cycle stream is not in a state this page will read. */
  reviewedAt: string | null;
  /** This security's weight in the account, as the same completed cycle
      recorded it — never a fresh account call. Null where that cycle
      did not hold it, which is not a zero. */
  holding: RecordedHolding | null;
}

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

/**
 * An instant, read by a person.
 *
 * The cycle store carries `finished_at` as an ISO timestamp and the
 * backend words no sentence for it, so the old page printed
 * *"completed 2026-08-24T17:35:54.333901Z"* verbatim. This is
 * formatting and not computation: the same instant, to the minute, in
 * UTC because that is the zone it was recorded in — no locale, so a
 * server and a browser cannot disagree, and no relative phrasing, which
 * would age between render and reading.
 *
 * A string that does not parse is returned untouched rather than
 * guessed at.
 */
export function statedInstant(iso: string | null): string | null {
  if (!iso) {
    return null;
  }

  const at = new Date(iso);

  if (Number.isNaN(at.getTime())) {
    return iso;
  }

  const minutes = at.getUTCMinutes().toString().padStart(2, "0");
  const hours = at.getUTCHours().toString().padStart(2, "0");

  return `${at.getUTCDate()} ${MONTHS[at.getUTCMonth()]} ${at.getUTCFullYear()}, ${hours}:${minutes} UTC`;
}

export function heroModel(
  dossier: DossierViewModel,
  review: CycleReview | null,
  reviewedAt: string | null,
): HeroModel {
  const industry = dossier.classification?.industry ?? null;

  return {
    symbol: dossier.symbol,
    industry:
      industry && industry.label
        ? {
            label: industry.label,
            sector: industry.sector,
            stated: industry.stated,
            age: industry.read?.age ?? null,
          }
        : null,
    reviewedAt: statedInstant(reviewedAt),
    holding:
      review?.portfolio?.holdings.find(
        (entry) => entry.symbol === dossier.symbol,
      ) ?? null,
  };
}

// ── the course ──────────────────────────────────────────────────────

export interface CourseModel {
  /** The action, verbatim from the action carrier. Primary. */
  statement: string;
  /** The decision state. Secondary — it labels the course, never
      produces it. */
  disposition: string;
  /** Why the case qualifies or stops, in the decision's own words. */
  because: string;
  /** The next catalyst or review event. Null where none is recorded. */
  checkpoint: string | null;
}

/**
 * The course, or nothing.
 *
 * **Null is a real answer.** Where the dossier carries no action, this
 * returns null and the surface shows the disposition with a stated
 * absence — it does not turn `PREPARE` into *"wait"*, or `RECOMMEND`
 * into *"buy"*. Those words belong to the action carrier, which is
 * produced by the decision layer and worded by it.
 *
 * `because` is the dossier's own — computed for this request — and
 * never the blocker sentence recorded in an older cycle. Two reasons,
 * both load-bearing: a stale explanation beside a fresh decision is the
 * same defect as a stale envelope beside one, and the recorded blocker
 * is written as a score comparison ("valuation scores 55 against the 60
 * a recommendation needs") which the specification forbids as the
 * explanation. The dossier says the investor-facing half of the same
 * fact: *"The company is attractive, but valuation does not currently
 * support action."*
 */
export function courseModel(dossier: DossierViewModel): CourseModel | null {
  const action = dossier.action;

  if (!action || !action.statement) {
    return null;
  }

  return {
    statement: action.statement,
    disposition: dossier.decisionState,
    because: action.because || dossier.rationale,
    checkpoint: action.checkpoint,
  };
}

// ── capital consideration ───────────────────────────────────────────

export interface CapitalModel {
  course: CycleCourse;
  finishedAt: string;
}

/**
 * The envelope the latest completed review recorded, or nothing.
 *
 * A thin selector on purpose: the envelope's own sentence, its
 * constraints, its liquidity limitation and the full disclaimer are
 * rendered by the component the homepage already uses, and nothing here
 * reads `finalPct`, decides whether it means a total position or
 * additional room, or recomputes anything.
 *
 * A course with no envelope returns null, so a non-capital course
 * renders no shell and implies no zero capacity.
 */
export function capitalModel(
  recorded: { course: CycleCourse; finishedAt: string } | null,
): CapitalModel | null {
  if (!recorded || !recorded.course.envelope) {
    return null;
  }

  return recorded;
}

// ── the three summary widgets ───────────────────────────────────────

const SUMMARY_LIMIT = 3;

export interface SummaryItem {
  stated: string;
  /** Where this came from — the decision itself, or an analyst reading. */
  origin: "decision" | "assessed";
}

/**
 * Decision-owned statements first, analyst prose second, capped at
 * three and never duplicated.
 *
 * The two lists genuinely overlap — `synthesis.because` is drawn from
 * `strengths` and `synthesis.despite` from `risks` — so topping up
 * without deduplicating would print the same sentence twice and call
 * the second one a different kind of evidence.
 */
function merged(
  owned: readonly string[],
  assessed: readonly string[],
  seen: Set<string>,
): readonly SummaryItem[] {
  const items: SummaryItem[] = [];

  for (const stated of owned) {
    if (stated && !seen.has(stated)) {
      seen.add(stated);
      items.push({ stated, origin: "decision" });
    }
  }

  for (const stated of assessed) {
    if (stated && !seen.has(stated)) {
      seen.add(stated);
      items.push({ stated, origin: "assessed" });
    }
  }

  return items.slice(0, SUMMARY_LIMIT);
}

export interface SummaryWidgets {
  qualifies: readonly SummaryItem[];
  wrong: readonly SummaryItem[];
  changes: readonly SummaryItem[];
}

/**
 * The three widgets, computed together so they partition rather than
 * repeat.
 *
 * **The corpus forced this.** On AMD, `invalidationConditions` is the
 * same three sentences as `risks` — *"AMD declined -3.28%"*, *"Short-term
 * price momentum is strongly negative"*, *"Annualised volatility is
 * 71.8%"* — so computing the widgets independently rendered one list
 * twice, under *"What could go wrong"* and again under *"What changes
 * the view"*. Two headings over identical content is worse than one:
 * it implies the platform holds two findings where it holds one.
 *
 * So a statement is claimed by the first widget entitled to it, in the
 * order an investor reads them, and a widget left with nothing is
 * omitted. That omission is the honest answer — where every recorded
 * review condition is already a stated risk, this platform has nothing
 * *additional* to say about what would change the view, and a repeated
 * list would not be saying it either.
 */
export function summaryWidgets(dossier: DossierViewModel): SummaryWidgets {
  const seen = new Set<string>();

  return {
    qualifies: merged(
      (dossier.synthesis?.because ?? []).map((fact) => fact.statement),
      dossier.strengths,
      seen,
    ),
    wrong: merged(
      (dossier.synthesis?.despite ?? []).map((fact) => fact.statement),
      dossier.risks,
      seen,
    ),
    changes: merged(
      (dossier.synthesis?.reviewIf ?? []).map((item) => item.condition),
      dossier.invalidationConditions,
      seen,
    ),
  };
}

/** Why the case qualifies — what the decision stood on, then what an
    analyst observed. Never the account's or the market's condition. */
export function whyItQualifies(
  dossier: DossierViewModel,
): readonly SummaryItem[] {
  return summaryWidgets(dossier).qualifies;
}

/** What could go wrong or block progress. The blocker itself belongs to
    the course block above — one kind of information, one owner — so
    this carries what the case runs *despite*, then the analyst's own
    risks. Account and market risks are excluded by construction. */
export function whatCouldGoWrong(
  dossier: DossierViewModel,
): readonly SummaryItem[] {
  return summaryWidgets(dossier).wrong;
}

/** What would change the view, beyond what is already stated as a risk.
    The condition's own sentence: `wouldChange` names what it would
    change and belongs beside the dated record, not in a three-item
    widget — carrying it here would make each row two claims. */
export function whatChangesTheView(
  dossier: DossierViewModel,
): readonly SummaryItem[] {
  return summaryWidgets(dossier).changes;
}

// ── review history, one line ────────────────────────────────────────

/**
 * The single line the Overview may say about review history.
 *
 * The dated record is a separate view. What belongs beside a current
 * course is whether it has been moving, in the backend's own sentence —
 * or that it has not, which a count of reviews states honestly without
 * implying a duration of coverage.
 */
export function historyLine(dossier: DossierViewModel): string | null {
  const course = dossier.decisionCourse;

  if (!course) {
    return null;
  }

  if (course.changes > 0) {
    return course.stated;
  }

  if (course.reviews > 0) {
    return `Unchanged across ${course.reviews} recorded review${
      course.reviews === 1 ? "" : "s"
    }.`;
  }

  return course.absentBecause;
}

// ── financial snapshot ──────────────────────────────────────────────

/** Which authorities the Overview snapshot admits, and how each is
    worded. Taken from the backend's own standing vocabulary — this side
    maps a token to a label and invents no third state. */
const AUTHORITY_LABELS: Record<string, string> = {
  filing_evidence: "Filing evidence",
  provider_fallback: "Provider reported",
  last_known_provider_fallback: "Last known",
  refused: "Refused",
};

/**
 * A figure, formatted from its own value, unit and currency.
 *
 * Moved here from the page rather than copied: the Financials view and
 * the Overview snapshot must render the same number the same way, and
 * two implementations of one formatting rule is how they stop doing
 * that.
 *
 * Note what this is *not* reading. `row.stated` is the arithmetic as
 * the filing states it — *"Total revenues" 94,425 under "2025" against
 * 91,361 under "2024"* — and it is evidence, not a value. Rendering it
 * as the figure blew a compact row 180px past the viewport and, worse,
 * put a sentence where the reader expected a number.
 */
export function formattedFigure(row: {
  value: number | null;
  unit: string | null;
  currency: string | null;
}): string | null {
  if (row.value === null) {
    return null;
  }

  if (row.unit === "fraction") {
    return `${(row.value * 100).toFixed(1)}%`;
  }

  if (row.unit === "currency") {
    const compact = compactAmount(row.value);

    return row.currency ? `${row.currency} ${compact}` : compact;
  }

  return `${row.value.toFixed(2)}x`;
}

export function compactAmount(value: number): string {
  const magnitude = Math.abs(value);

  if (magnitude >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}bn`;
  }

  if (magnitude >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}m`;
  }

  return value.toLocaleString("en-US");
}

export interface SnapshotFact {
  label: string;
  /** The figure, formatted from its value. Never the arithmetic. */
  stated: string;
  authority: string;
  authorityKey: string;
  age: string | null;
  currency: string | null;
  period: string | null;
}

export interface SnapshotModel {
  facts: readonly SnapshotFact[];
  /** One sentence about what is not held, said once. The per-metric
      accounts live in the Financials view. */
  coverage: string | null;
}

/**
 * The decision-relevant figures already held, each under its own
 * authority.
 *
 * **A provider fallback never becomes filing evidence**, and the two
 * growth metrics are never compared: the backend already names them
 * apart — *"Revenue growth — FY filing"* against *"Provider-reported
 * revenue growth — period not stated"* — and this side preserves both
 * labels exactly. Disney's filing earnings growth of +132.7% and the
 * provider's −48.3% reading are different measurements of different
 * periods under different formulas, and nothing here invites the reader
 * to subtract one from the other.
 *
 * A row with no value is omitted and counted, so the Overview is not a
 * wall of absent metrics; a zero is a value and stays.
 */
export function snapshotModel(dossier: DossierViewModel): SnapshotModel {
  const rows = dossier.fundamentals?.rows ?? [];
  const facts: SnapshotFact[] = [];
  let absent = 0;

  for (const row of rows) {
    const figure = formattedFigure(row);

    // Held on the value, not on the sentence: a zero is a value and
    // stays, and a row whose arithmetic is absent is an absence.
    if (figure === null) {
      absent += 1;
      continue;
    }

    facts.push({
      label: row.label,
      stated: figure,
      authority: AUTHORITY_LABELS[row.standing] ?? row.standing,
      authorityKey: row.standing,
      age: row.asOf,
      currency: row.currency,
      period: row.period,
    });
  }

  return {
    facts,
    coverage:
      absent > 0
        ? `${absent} of ${rows.length} figures are not held. Each one, and why, is in Financials.`
        : null,
  };
}
