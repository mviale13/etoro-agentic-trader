import Link from "next/link";
import type { ReactNode } from "react";

import type {
  DecisionTrendViewModel,
  ExecutiveActionViewModel,
} from "@/lib/view-models/investment-case";

/**
 * The one way an Artificial CIO decision presents itself.
 *
 * Every surface that shows a decision — the Overview's investment cases,
 * the Research pipeline, and any future Decisions inbox — renders this
 * same identity: security, decision state, the CIO's conviction in the
 * backend's own words, the recorded history, and a review action. What
 * differs between surfaces goes in `children`; what identifies a decision
 * does not differ.
 *
 * This component formats values the backend measured and worded. It bands
 * nothing and decides nothing.
 */
interface DecisionCardProps {
  rank?: number;
  symbol: string;
  /** The security's name, where the backend provides one. */
  name?: string;
  /** Decision state, e.g. RECOMMEND, PREPARE, INVESTIGATE — never
   *  translated into trading language. The investor decides. */
  decisionState: string;
  conviction: number;
  /** The conviction put into words by the backend. */
  convictionLabel: string;
  /** Short labels such as the watchlist that names this security. */
  tags?: readonly string[];
  /**
   * Which way the case has been moving, as recorded. Null renders
   * nothing at all: a first decision claims no history, and a first
   * review is not a stable one.
   */
  trend: DecisionTrendViewModel | null;
  /** What to consider doing. Null renders nothing. */
  action?: ExecutiveActionViewModel | null;
  reviewHref: string;
  children?: ReactNode;
}

/** Direction as a mark, so the eye reads it before the sentence. */
const TREND_MARK: Record<string, string> = {
  stable: "→",
  improving: "↑",
  deteriorating: "↓",
};

export function DecisionCard({
  rank,
  symbol,
  name,
  decisionState,
  conviction,
  convictionLabel,
  tags = [],
  trend,
  action = null,
  reviewHref,
  children,
}: DecisionCardProps) {
  return (
    <article className="group relative flex h-full flex-col overflow-hidden rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_18px_60px_-36px_rgba(15,23,42,0.45)] transition duration-300 hover:-translate-y-0.5 hover:border-slate-300">
      <div className="flex items-start justify-between gap-5">
        <div className="flex items-center gap-3">
          {rank !== undefined ? (
            <span className="flex size-10 shrink-0 items-center justify-center rounded-full border border-slate-200 text-sm font-semibold text-slate-700">
              {String(rank).padStart(2, "0")}
            </span>
          ) : null}

          <div>
            <h3 className="text-2xl font-semibold tracking-tight text-slate-950">
              {symbol}
            </h3>

            {name && name !== symbol ? (
              <p className="mt-0.5 text-sm text-slate-500">{name}</p>
            ) : null}

            {tags.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full border border-slate-200 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        </div>

        <span className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700">
          {decisionState}
        </span>
      </div>

      <div className="mt-7">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">
              Executive conviction
            </p>

            <span className="mt-1 block text-4xl font-semibold tracking-[-0.05em] text-slate-950">
              {conviction}%
            </span>
          </div>

          <p className="max-w-36 text-right text-sm font-medium leading-5 text-slate-600">
            {convictionLabel}
          </p>
        </div>

        <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-slate-950"
            style={{ width: `${conviction}%` }}
          />
        </div>
      </div>

      {children}

      {/* What to consider doing — not the decision state renamed. A
          RECOMMEND on something already held asks a different question
          from a RECOMMEND on something the investor does not own. */}
      {action ? (
        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-sm font-semibold text-slate-950">
            {action.statement}
          </p>

          <p className="mt-1.5 text-sm leading-6 text-slate-600">
            {action.because}
          </p>

          {action.checkpoint ? (
            <p className="mt-2 text-xs text-slate-500">
              Next: {action.checkpoint}
            </p>
          ) : null}
        </div>
      ) : null}

      {/* Absent until the CIO has judged this security at least once
          before. A first decision says nothing here, never "no change". */}
      {trend ? (
        <p className="mt-4 text-sm font-medium text-slate-600">
          <span aria-hidden className="mr-1.5">
            {TREND_MARK[trend.direction] ?? "•"}
          </span>

          {trend.stated}
        </p>
      ) : null}

      <div className="mt-auto flex items-center justify-end pt-7">
        <Link
          href={reviewHref}
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-950 transition group-hover:gap-3"
        >
          Review case
          <span aria-hidden="true">→</span>
        </Link>
      </div>
    </article>
  );
}
