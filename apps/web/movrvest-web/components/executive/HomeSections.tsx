import Link from "next/link";
import { Fragment } from "react";

import type {
  CycleCourse,
  CycleReview,
  RecordedAllocation,
  RecordedPortfolio,
} from "@/lib/api/cycle-review";

/**
 * The homepage's sections, in the owner's order.
 *
 * Each is its own section rather than one merged block — the only
 * merging asked for is *within* the holdings table, which carries what
 * changed as a column instead of as a separate list.
 *
 * There is no separate list of courses for *holdings*: the owner
 * removed it. Each holding's course is the table's own column, and the
 * review's "this asked for nothing" sentence stays on the status strip,
 * where it is the backend's wording rather than this page's.
 *
 * What the CIO evaluated *beyond* the holdings is two sections rather
 * than one ranked table. One table listing a waiting case, a research
 * case and two rejections under *"top opportunities"* presented four
 * different answers as four degrees of one answer.
 *
 * Every value here is carried from the recorded cycle. This file
 * chooses layout and plain wording and computes no analytics: no score,
 * no ranking, no classification and no verdict is produced in
 * TypeScript. Where the record says nothing, the page says nothing.
 */

const usd = new Intl.NumberFormat(undefined, {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

function money(value: number | null): string {
  return value === null ? "Unavailable" : usd.format(value);
}

function percent(value: number | null): string {
  return value === null ? "—" : `${value.toFixed(1)}%`;
}

function signedPercent(value: number | null): string {
  if (value === null) {
    return "—";
  }

  return `${value > 0 ? "+" : ""}${value.toFixed(1)} pts`;
}

const CARD = "rounded-3xl border border-slate-200 bg-white p-6 sm:p-7";
const HEAD = "text-sm font-semibold text-slate-900";
const CELL = "px-3 py-2.5 text-sm text-slate-700";
const TH =
  "px-3 py-2 text-left text-xs font-semibold uppercase tracking-[0.14em] text-slate-500";

// ── 1. portfolio snapshot ───────────────────────────────────────────

export function PortfolioSnapshot({
  portfolio,
}: {
  portfolio: RecordedPortfolio | null;
}) {
  if (!portfolio) {
    return (
      <section className={CARD}>
        <h2 className={HEAD}>Portfolio</h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review recorded no account reading, so nothing about your
          portfolio is shown. No figure stands in for one.
        </p>
      </section>
    );
  }

  const invested =
    portfolio.availableCashUsd === null
      ? null
      : portfolio.totalValue - portfolio.availableCashUsd;

  return (
    <section className={CARD}>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className={HEAD}>Portfolio</h2>

        {portfolio.observed ? (
          <p className="text-xs text-slate-500">{portfolio.observed}</p>
        ) : null}
      </div>

      <dl className="mt-4 grid gap-4 sm:grid-cols-3">
        {[
          ["Total value", usd.format(portfolio.totalValue)],
          ["Available cash", money(portfolio.availableCashUsd)],
          ["Invested", money(invested)],
        ].map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs uppercase tracking-[0.14em] text-slate-500">
              {label}
            </dt>
            <dd className="mt-1 text-2xl font-semibold tracking-[-0.02em] text-slate-950">
              {value}
            </dd>
          </div>
        ))}
      </dl>

      {portfolio.cashPct === null ? (
        <p className="mt-4 text-xs leading-5 text-slate-500">
          The cash share of the account is unavailable, so no split between
          cash and invested is shown.
        </p>
      ) : null}
    </section>
  );
}

// ── 2. holdings, ranked, with what changed as a column ──────────────

/**
 * Whether this review may claim any movement at all.
 *
 * Only a complete history compared against a real previous cycle can.
 * An incomplete stream or an unclassified day claims nothing — and
 * "Unchanged" is a finding, so it may never be the fallback.
 */
export function isComparable(review: CycleReview): boolean {
  return review.streamComplete && review.comparisonOutcome === "compared";
}

/** One security's movement label, or the honest refusal to give one. */
export function movementLabel(review: CycleReview, symbol: string): string {
  if (!isComparable(review)) {
    return "Not compared";
  }

  if (review.newlyProduced.includes(symbol)) return "New";
  if (review.changed.includes(symbol)) return "Changed";
  if (review.unchanged.includes(symbol)) return "Unchanged";

  return "—";
}

/**
 * One row per security, and the symbol is the row's identity.
 *
 * The record carries one holding per security — the cycle folds the
 * broker's per-trade positions before writing it, and the store folds
 * again on read — so `row.symbol` is a unique key rather than a
 * coincidentally-unique one. It is deliberately not made unique here
 * with an index: a duplicate would mean the record broke its own
 * contract, and React saying so is better than this table hiding it.
 * Nothing is deduplicated, summed or sorted in this component.
 */
export function HoldingsTable({ review }: { review: CycleReview }) {
  const portfolio = review.portfolio;

  const courses = new Map(review.courses.map((c) => [c.symbol, c]));

  const comparable = isComparable(review);

  function movement(symbol: string): string {
    return movementLabel(review, symbol);
  }

  const rows = (portfolio?.holdings ?? []).map((holding) => ({
    symbol: holding.symbol,
    weightPct: holding.weightPct,
    marketValueUsd: holding.marketValueUsd,
    course: courses.get(holding.symbol) ?? null,
  }));

  // Any security the review judged but the account no longer shows as a
  // holding is still listed: nothing the cycle covered disappears.
  const extra = review.courses
    .filter((course) => !rows.some((row) => row.symbol === course.symbol))
    .map((course) => ({
      symbol: course.symbol,
      weightPct: null,
      marketValueUsd: null as number | null,
      course,
    }));

  const all = [...rows, ...extra];

  return (
    <section className={CARD}>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className={HEAD}>
          Your {all.length} holding{all.length === 1 ? "" : "s"}, ranked
        </h2>

        {comparable ? null : (
          <p className="text-xs text-slate-500">
            No comparison with a previous review was possible, so no movement
            is claimed.
          </p>
        )}
      </div>

      {all.length === 0 ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review covered no securities.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse">
            <thead>
              <tr className="border-b border-slate-200">
                <th className={TH}>Security</th>
                <th className={TH}>Weight</th>
                <th className={TH}>Value</th>
                <th className={TH}>View</th>
                <th className={TH}>Course</th>
                <th className={TH}>Since last review</th>
              </tr>
            </thead>

            <tbody>
              {all.map((row) => (
                <Fragment key={row.symbol}>
                <tr className="border-b border-slate-100">
                  <td className={`${CELL} font-semibold text-slate-950`}>
                    <Link
                      className="underline decoration-slate-300 underline-offset-4 hover:decoration-slate-900"
                      href={`/dossiers/${encodeURIComponent(row.symbol)}`}
                    >
                      {row.symbol}
                    </Link>
                  </td>
                  <td className={CELL}>{percent(row.weightPct)}</td>
                  <td className={CELL}>
                    {row.marketValueUsd === null
                      ? "—"
                      : usd.format(row.marketValueUsd)}
                  </td>
                  <td className={CELL}>{row.course?.disposition ?? "—"}</td>
                  <td className={CELL}>
                    {row.course?.actionStatement ?? "No course recorded"}
                  </td>
                  <td className={CELL}>{movement(row.symbol)}</td>
                </tr>

                {/* The envelope belongs to this holding's course, so it
                    sits with it rather than in a column that would be
                    empty for every non-capital row. */}
                {row.course?.envelope ? (
                  <tr className="border-b border-slate-100">
                    <td className="px-3 pb-3" colSpan={6}>
                      <CourseEnvelope course={row.course} />
                    </td>
                  </tr>
                ) : null}
                </Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// ── 3. what the CIO evaluated, in two groups ────────────────────────

/**
 * How many rows of each group the page shows.
 *
 * The owner's number. What is dropped is named beneath the group
 * rather than silently truncated — a table that stops at three and
 * says nothing reads like a complete list of three.
 */
export const GROUP_ROWS = 3;

/**
 * The two groups, split on the platform's own bit.
 *
 * `asksForSomething` comes from the pipeline's `ActionKind` and is the
 * canonical answer to *does this ask the investor for anything*. It is
 * not re-derived from the decision state here, and it must not be: the
 * same state asks for different things depending on whether the
 * security is held, and three of the five rows on the live page are
 * REJECT or PREPARE cases whose courses differ.
 */
export function askingCourses(candidates: CycleCourse[]): CycleCourse[] {
  return candidates.filter((candidate) => candidate.asksForSomething);
}

export function blockedCases(candidates: CycleCourse[]): CycleCourse[] {
  return candidates.filter((candidate) => !candidate.asksForSomething);
}

/** The conviction, or the honest reason there is no figure to show. */
/**
 * What each asset class is called in the table.
 *
 * CSS `capitalize` rendered the field name "etfs" as "Etfs" — it
 * uppercases the first letter of a word and leaves the rest, which is
 * wrong for an initialism. The backend's own sentences already say
 * "ETFs", and this keeps the table agreeing with them.
 */
function assetLabel(asset: string): string {
  const labels: Record<string, string> = {
    stocks: "Stocks",
    etfs: "ETFs",
    crypto: "Crypto",
    cash: "Cash",
  };

  return labels[asset] ?? asset;
}

/**
 * Which of the three strategy cards this review earns.
 *
 * `plan` renders the targets, ranges, standings, total and compliance;
 * `policy-refused` renders the backend's refusal and the measured
 * account with none of those; `no-comparison` is a review that
 * recorded no allocation at all.
 *
 * Exported because it *is* the decision — the component branches on
 * this and nothing else, so a test of this function is a test of what
 * the page shows. The defect it exists to prevent: a refused policy
 * rendering an independently mapped plan, targets and all.
 */
export type StrategyCardShape = "plan" | "policy-refused" | "no-comparison";

export function strategyCardShape(
  portfolio: RecordedPortfolio | null,
): StrategyCardShape {
  if (portfolio?.allocationPolicyRefused) {
    return "policy-refused";
  }

  if (!portfolio || portfolio.allocations.length === 0) {
    return "no-comparison";
  }

  return "plan";
}

/**
 * The four targets added up, or nothing where any target is missing.
 *
 * A missing target is not zero, so it cannot be summed into a total.
 * Returning null renders a dash — the same absence the rest of this
 * table uses — rather than a figure the plan never stated.
 */
export function targetTotal(allocations: RecordedAllocation[]): number | null {
  if (allocations.some((item) => item.targetPct === null)) {
    return null;
  }

  return allocations.reduce((sum, item) => sum + (item.targetPct ?? 0), 0);
}

/** The operating range as the investor reads it, or a dash. */
function operatingRange(allocation: RecordedAllocation): string {
  if (allocation.minimumPct === null || allocation.maximumPct === null) {
    return "\u2014";
  }

  return `${allocation.minimumPct}\u2013${allocation.maximumPct}%`;
}

/** The standing in the investor's words. Never a colour-coded verdict. */
function standingLabel(standing: string): string {
  const labels: Record<string, string> = {
    below_range: "Below range",
    within_range: "Within range",
    above_range: "Above range",
    unmeasured: "Not measured",
  };

  return labels[standing] ?? "\u2014";
}

/**
 * Why there is no strategic plan to compare against, said once.
 *
 * The backend's own sentence, verbatim. This component states no
 * consequence of its own and repairs nothing: a strategy the platform
 * could not validate is reported as unvalidated, and the alternative —
 * which shipped before this — was a table of targets no owner stated.
 */
function PolicyRefusal({ reason }: { reason: string }) {
  return (
    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
      <p className="text-xs uppercase tracking-[0.14em] text-amber-700">
        No strategic allocation was applied
      </p>

      <p className="mt-1 text-sm leading-6 text-slate-800">{reason}</p>

      <p className="mt-2 text-xs leading-5 text-slate-600">
        No targets, operating ranges, standings or compliance judgment are
        shown, because this review validated no plan to state them from.
      </p>
    </div>
  );
}

/**
 * The CIO's account of the account's shape.
 *
 * Rendered from the completed cycle's own record — this component
 * composes nothing. It is guidance about allocation and never an
 * instruction: it names no security, proposes no trade and sizes
 * nothing, because allocation drift authorizes none of those.
 */
function AllocationGuidance({ portfolio }: { portfolio: RecordedPortfolio }) {
  const text =
    portfolio.allocationGuidance || portfolio.allocationGuidanceRefused;

  if (!text) {
    return null;
  }

  return (
    <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-500">
        What the CIO says about this shape
      </p>

      <p className="mt-1 text-sm leading-6 text-slate-800">{text}</p>
    </div>
  );
}

export function convictionCell(candidate: CycleCourse): string {
  if (candidate.conviction === null) {
    return candidate.convictionBasis || "Not stated";
  }

  // A number with no account of itself is not shown as a number. 40
  // beside nothing reads as enthusiasm, and it is a state-capped
  // decision score.
  if (!candidate.convictionBasis) {
    return "Not stated";
  }

  return `${candidate.conviction} (${candidate.disposition})`;
}

/**
 * What blocks progress, in the deciding layer's own words.
 *
 * Never an em dash where a case is blocked, and never a sentence this
 * page composed. A record written before blockers existed says so
 * instead of claiming there is nothing in the way.
 */
export function blockerCell(candidate: CycleCourse): string {
  if (candidate.blocker === null) {
    return "Not recorded for this review";
  }

  return candidate.blocker.stated;
}

/**
 * The Capital Action Envelope beside the course it belongs to.
 *
 * The backend's own sentence, rendered as written — an upward bound, a
 * reduction floor, a zero-capacity statement or a refusal, each already
 * worded by the domain. Nothing here computes, compares or converts:
 * no currency amount, no share quantity, no order control.
 *
 * It belongs to the cycle whose course this is. A page that recomputed
 * one would be answering a question the recorded review did not ask.
 */
export function CourseEnvelope({ course }: { course: CycleCourse }) {
  const envelope = course.envelope;

  if (!envelope) {
    return null;
  }

  return (
    <div className="mt-3 rounded-xl border border-slate-200 bg-white p-3">
      <p className="text-xs uppercase tracking-[0.14em] text-slate-500">
        Capital consideration
      </p>

      <p className="mt-1 text-sm leading-6 text-slate-800">{envelope.stated}</p>

      {envelope.securityRiskBecause ? (
        <p className="mt-1 text-xs leading-5 text-slate-500">
          {envelope.securityRiskBecause}
        </p>
      ) : null}

      {envelope.namedGaps.length > 0 ? (
        <p className="mt-1 text-xs leading-5 text-slate-600">
          What limits this consideration — and it limits the action, not the
          company: {envelope.namedGaps.join("; ")}
        </p>
      ) : null}

      <p className="mt-1 text-xs leading-5 text-slate-500">
        A policy consideration bound, not an order, a target, or a
        recommendation to transact. {envelope.liquidity}
      </p>
    </div>
  );
}

function CaseRows({ cases }: { cases: CycleCourse[] }) {
  return (
    <div className="mt-4 grid gap-3">
      {cases.map((candidate) => (
        <article
          className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
          key={candidate.symbol}
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <Link
              className="text-base font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-900"
              href={`/dossiers/${encodeURIComponent(candidate.symbol)}`}
            >
              {candidate.symbol}
            </Link>

            <span className="text-xs uppercase tracking-[0.16em] text-slate-500">
              {candidate.disposition}
            </span>
          </div>

          <p className="mt-2 text-sm leading-6 text-slate-800">
            {candidate.actionStatement || "No course recorded"}
          </p>

          {candidate.actionBecause ? (
            <p className="mt-1 text-sm leading-6 text-slate-600">
              {candidate.actionBecause}
            </p>
          ) : null}

          <dl className="mt-3 grid gap-2 text-sm leading-6">
            <div>
              <dt className="text-xs uppercase tracking-[0.14em] text-slate-500">
                What blocks progress
              </dt>
              <dd className="text-slate-800">{blockerCell(candidate)}</dd>
            </div>

            <div>
              <dt className="text-xs uppercase tracking-[0.14em] text-slate-500">
                Conviction
              </dt>
              <dd className="text-slate-800">{convictionCell(candidate)}</dd>
              {candidate.convictionBasis ? (
                <dd className="text-xs leading-5 text-slate-500">
                  {candidate.convictionBasis}
                </dd>
              ) : null}
            </div>
          </dl>

          {/* What the ruling does not claim, and the analyst verdicts
              that survive it. Both are the backend's sentences. */}
          {candidate.blocker && candidate.blocker.doesNotSay ? (
            <p className="mt-2 text-xs leading-5 text-slate-500">
              {candidate.blocker.doesNotSay}
            </p>
          ) : null}

          {candidate.blocker && candidate.blocker.despite.length > 0 ? (
            <p className="mt-1 text-xs leading-5 text-slate-500">
              Still visible: {candidate.blocker.despite.join(" · ")}
            </p>
          ) : null}

          <CourseEnvelope course={candidate} />
        </article>
      ))}
    </div>
  );
}

/**
 * What was left out, and whether the ones shown were chosen or merely first.
 *
 * A truncated list makes its order decision-bearing: which three of five
 * an investor sees is a claim about which three matter. Where the
 * review's convictions were computed over different score families that
 * claim has no basis — the numbers are not on one scale — so the page
 * says the order is not a ranking rather than letting the cut imply one.
 */
function Dropped({ total, ranked }: { total: number; ranked: boolean }) {
  const truncated = total > GROUP_ROWS;

  if (!truncated && ranked) {
    return null;
  }

  return (
    <p className="mt-3 text-xs leading-5 text-slate-500">
      {truncated
        ? `${total - GROUP_ROWS} more not shown here. A list that stopped at ` +
          `${GROUP_ROWS} without saying so would read as the whole of what ` +
          "the review found."
        : null}
      {truncated && !ranked ? " " : null}
      {ranked
        ? null
        : "These are listed by symbol, not ranked: their convictions were " +
          "measured over different score families, so the numbers are not " +
          "on one scale and no order of merit is claimed."}
    </p>
  );
}

export function Opportunities({
  candidates,
  ranked,
}: {
  candidates: CycleCourse[];
  ranked: boolean;
}) {
  const asking = askingCourses(candidates);
  const blocked = blockedCases(candidates);

  if (candidates.length === 0) {
    return (
      <section className={CARD}>
        <h2 className={HEAD}>What the CIO evaluated beyond your holdings</h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review evaluated no securities outside your portfolio. That is a
          statement about what was reviewed — not a finding that nothing is
          worth considering. Run a cycle with a candidate budget to have them
          evaluated.
        </p>
      </section>
    );
  }

  return (
    <div className="grid gap-6">
      <section className={CARD}>
        <h2 className={HEAD}>Courses to consider</h2>

        {asking.length === 0 ? (
          <p className="mt-2 text-sm leading-6 text-slate-600">
            None of the securities reviewed beyond your holdings asks anything
            of you. That describes what this review found.
          </p>
        ) : (
          <>
            <CaseRows cases={asking.slice(0, GROUP_ROWS)} />
            <Dropped total={asking.length} ranked={ranked} />
            <p className="mt-3 text-xs leading-5 text-slate-500">
              A course to consider, not an instruction. Nothing is placed for
              you.
            </p>
          </>
        )}
      </section>

      <section className={CARD}>
        <h2 className={HEAD}>Cases blocked or refused</h2>

        {blocked.length === 0 ? (
          <p className="mt-2 text-sm leading-6 text-slate-600">
            Nothing the review evaluated beyond your holdings was blocked.
          </p>
        ) : (
          <>
            <CaseRows cases={blocked.slice(0, GROUP_ROWS)} />
            <Dropped total={blocked.length} ranked={ranked} />
            <p className="mt-3 text-xs leading-5 text-slate-500">
              A blocked case is not a bad business. Each blocker names the gate
              that stopped it, and a gate about price behaviour, cost or fit
              says nothing about the company.
            </p>
          </>
        )}
      </section>
    </div>
  );
}

// ── 4. portfolio against the investor's strategy ────────────────────

export function StrategyCard({
  portfolio,
}: {
  portfolio: RecordedPortfolio | null;
}) {
  const shape = strategyCardShape(portfolio);

  if (portfolio === null || shape === "no-comparison") {
    return (
      <section className={CARD}>
        <h2 className={HEAD}>Your portfolio against your strategy</h2>

        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review recorded no comparison against your Investment Policy, so
          none is shown.
        </p>
      </section>
    );
  }

  // No validated allocation policy, so no plan is shown: the refusal in
  // the backend's own words, and the account as this review measured it.
  // Nothing here reconstructs a target, a range, a standing, a total or
  // a compliance judgment — there is no plan to state one from.
  if (shape === "policy-refused") {
    return (
      <section className={CARD}>
        <h2 className={HEAD}>Your portfolio against your strategy</h2>

        <PolicyRefusal reason={portfolio.allocationPolicyRefused} />

        {portfolio.allocations.length > 0 ? (
          <>
            <p className="mt-4 text-xs uppercase tracking-[0.14em] text-slate-500">
              What this review measured
            </p>

            <div className="mt-2 overflow-x-auto">
              <table className="w-full min-w-[320px] border-collapse">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className={TH}>Allocation</th>
                    <th className={TH}>Now</th>
                  </tr>
                </thead>

                <tbody>
                  {portfolio.allocations.map((allocation) => (
                    <tr
                      className="border-b border-slate-100"
                      key={allocation.asset}
                    >
                      <td className={`${CELL} text-slate-950`}>
                        {assetLabel(allocation.asset)}
                      </td>
                      <td className={CELL}>{percent(allocation.currentPct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="mt-3 text-xs leading-5 text-slate-500">
              These are measurements of your account. They are shown without a
              target because your strategy states none that this review could
              validate.
            </p>
          </>
        ) : null}
      </section>
    );
  }

  return (
    <section className={CARD}>
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className={HEAD}>Your portfolio against your strategy</h2>

        <p className="text-xs text-slate-500">
          {portfolio.compliant === null
            ? "Some comparisons could not be made, so compliance is not stated."
            : portfolio.compliant
              ? "Every measured allocation is within its band."
              : "At least one measured allocation is outside its band."}
        </p>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[520px] border-collapse">
          <thead>
            <tr className="border-b border-slate-200">
              <th className={TH}>Allocation</th>
              <th className={TH}>Now</th>
              <th className={TH}>Strategic target</th>
              <th className={TH}>Operating range</th>
              <th className={TH}>Standing</th>
            </tr>
          </thead>

          <tbody>
            {portfolio.allocations.map((allocation) => (
              <tr className="border-b border-slate-100" key={allocation.asset}>
                <td className={`${CELL} text-slate-950`}>
                  {assetLabel(allocation.asset)}
                </td>
                <td className={CELL}>{percent(allocation.currentPct)}</td>
                <td className={CELL}>{percent(allocation.targetPct)}</td>
                <td className={CELL}>{operatingRange(allocation)}</td>
                <td className={CELL}>{standingLabel(allocation.standing)}</td>
              </tr>
            ))}
          </tbody>

          {/* The targets are a plan, so the page shows that they add
              up. A set of targets totalling anything but 100% is a
              broken plan, and the reader is the one who should see it
              — this account rendered 0/0/0/5 for as long as the mapper
              was allowed to invent three of the four.

              Reached only with a validated plan in hand, and it never
              sums a missing target into a total: a refused policy has
              already returned above, and a "Total 0%" would be the
              same invention under a different name. */}
          <tfoot>
            <tr>
              <td className={`${CELL} font-semibold text-slate-950`}>Total</td>
              <td className={CELL} />
              <td className={`${CELL} font-semibold text-slate-950`}>
                {percent(targetTotal(portfolio.allocations))}
              </td>
              <td className={CELL} />
              <td className={CELL} />
            </tr>
          </tfoot>
        </table>
      </div>

      <AllocationGuidance portfolio={portfolio} />

      {portfolio.allocations.some((a) => a.differencePct === null) ? (
        <p className="mt-3 text-xs leading-5 text-slate-500">
          A dash is an allocation that could not be read. It is not an
          allocation sitting on its target.
        </p>
      ) : null}
    </section>
  );
}
