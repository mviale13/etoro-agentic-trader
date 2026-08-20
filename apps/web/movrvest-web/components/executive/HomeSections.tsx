import Link from "next/link";

import type {
  CycleCourse,
  CycleReview,
  RecordedPortfolio,
} from "@/lib/api/cycle-review";

/**
 * The homepage's five sections, in the owner's order.
 *
 * Each is its own section rather than one merged block — the only
 * merging asked for is *within* the holdings table, which carries what
 * changed as a column instead of as a separate list.
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

// ── 2. executive actions ────────────────────────────────────────────

export function ExecutiveActions({ review }: { review: CycleReview }) {
  const asking = review.courses.filter((course) => course.asksForSomething);

  return (
    <section className={CARD}>
      <h2 className={HEAD}>What the Artificial CIO suggests you consider</h2>

      {asking.length === 0 ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review asked for nothing. That describes what it found, and is
          not an assessment that your portfolio is safe.
        </p>
      ) : (
        <ul className="mt-4 grid gap-3">
          {asking.map((course) => (
            <li
              className="rounded-2xl border border-slate-200 bg-slate-50 p-4"
              key={course.symbol}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <Link
                  className="text-base font-semibold text-slate-950 underline decoration-slate-300 underline-offset-4 hover:decoration-slate-900"
                  href={`/dossiers/${encodeURIComponent(course.symbol)}`}
                >
                  {course.symbol}
                </Link>

                <span className="text-xs uppercase tracking-[0.16em] text-slate-500">
                  {course.disposition}
                </span>
              </div>

              <p className="mt-2 text-sm leading-6 text-slate-800">
                {course.actionStatement}
              </p>

              {course.actionBecause ? (
                <p className="mt-1 text-sm leading-6 text-slate-600">
                  {course.actionBecause}
                </p>
              ) : null}

              {course.envelope ? (
                <p className="mt-2 text-sm leading-6 text-slate-700">
                  {course.envelope.stated}
                </p>
              ) : null}

              {course.envelope && course.envelope.namedGaps.length > 0 ? (
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Limits the action, not the company:{" "}
                  {course.envelope.namedGaps.join("; ")}
                </p>
              ) : null}

              <p className="mt-2 text-xs leading-5 text-slate-500">
                A course to consider, not an instruction. Nothing is placed for
                you.
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// ── 3. holdings, ranked, with what changed as a column ──────────────

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

/** The five the CIO ranked highest. The order is the server's, not ours. */
export function topOpportunities(candidates: CycleCourse[]): CycleCourse[] {
  return candidates.slice(0, 5);
}

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
                <tr className="border-b border-slate-100" key={row.symbol}>
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
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

// ── 4. top five opportunities ───────────────────────────────────────

export function Opportunities({ candidates }: { candidates: CycleCourse[] }) {
  const top = topOpportunities(candidates);

  return (
    <section className={CARD}>
      <h2 className={HEAD}>Top opportunities the CIO evaluated</h2>

      {top.length === 0 ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review evaluated no securities outside your portfolio, so there
          is nothing to rank. That is a statement about what was reviewed — not
          a finding that nothing is worth considering. Run a cycle with a
          candidate budget to have them evaluated.
        </p>
      ) : (
        <>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] border-collapse">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className={TH}>Security</th>
                  <th className={TH}>Conviction</th>
                  <th className={TH}>Course</th>
                  <th className={TH}>What is missing</th>
                </tr>
              </thead>

              <tbody>
                {top.map((candidate) => (
                  <tr className="border-b border-slate-100" key={candidate.symbol}>
                    <td className={`${CELL} font-semibold text-slate-950`}>
                      <Link
                        className="underline decoration-slate-300 underline-offset-4 hover:decoration-slate-900"
                        href={`/dossiers/${encodeURIComponent(candidate.symbol)}`}
                      >
                        {candidate.symbol}
                      </Link>
                    </td>
                    <td className={CELL}>
                      {candidate.conviction === null
                        ? "Not stated"
                        : candidate.conviction}
                    </td>
                    <td className={CELL}>
                      {candidate.actionStatement || "No course recorded"}
                    </td>
                    <td className={CELL}>
                      {candidate.envelope &&
                      candidate.envelope.namedGaps.length > 0
                        ? candidate.envelope.namedGaps.join("; ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs leading-5 text-slate-500">
            Ordered by the conviction the Artificial CIO assigned. Conviction
            expresses priority, not certainty — it can be higher on a security
            less evidence was found for, which is why what is missing is shown
            beside it.
          </p>
        </>
      )}
    </section>
  );
}

// ── 5. portfolio against the investor's strategy ────────────────────

export function StrategyCard({
  portfolio,
}: {
  portfolio: RecordedPortfolio | null;
}) {
  if (!portfolio || portfolio.allocations.length === 0) {
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
              <th className={TH}>Target</th>
              <th className={TH}>Difference</th>
            </tr>
          </thead>

          <tbody>
            {portfolio.allocations.map((allocation) => (
              <tr className="border-b border-slate-100" key={allocation.asset}>
                <td className={`${CELL} capitalize text-slate-950`}>
                  {allocation.asset}
                </td>
                <td className={CELL}>{percent(allocation.currentPct)}</td>
                <td className={CELL}>{percent(allocation.targetPct)}</td>
                <td className={CELL}>
                  {signedPercent(allocation.differencePct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {portfolio.allocations.some((a) => a.differencePct === null) ? (
        <p className="mt-3 text-xs leading-5 text-slate-500">
          A dash is an allocation that could not be read. It is not an
          allocation sitting on its target.
        </p>
      ) : null}
    </section>
  );
}
