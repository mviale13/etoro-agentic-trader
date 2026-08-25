/**
 * Token supply, in the order an investor reads it.
 *
 * Four sections, and the order is the product: what MOVRvest can say,
 * what remains unsettled, the source detail, then the full comparison
 * audit. Before this the page opened with fourteen claim cards and ten
 * pairwise comparison cards — the protocol maximum in six boxes, four
 * circulating readings in six conflict cards — and an investor met the
 * evidence inventory before any answer.
 *
 * **Nothing was deleted.** Every claim, comparison, caveat and
 * unresolved sentence is still on the page; three of the four sections
 * are native `<details>` so the default view is an answer and the
 * inventory is one keystroke away.
 *
 * "What MOVRvest can say" rather than "knows": the platform holds
 * provider claims here, and the heading keeps that boundary.
 */

import type { SupplyView } from "@/lib/api/crypto-dossier";
import {
  type SupplyGroup,
  type SupplyRow,
  supplyModel,
} from "@/components/crypto/supply-model";

/** The one prominent container. Everything below it is dividers and
    whitespace: the ruling's four-box ceiling is met by having one. */
const PANEL = "rounded-2xl border border-slate-200 bg-white";

const HEAD = "text-xs font-semibold uppercase tracking-[0.14em] text-slate-500";

// ── 1. what MOVRvest can say ────────────────────────────────────────

/**
 * The summary. One row per typed concept, the figure where the
 * evidence permits one and "Not settled" where it does not.
 *
 * "Not settled" is a state, not an error: it takes the same weight as
 * every other row, no colour of its own and no warning shape. What
 * would be dishonest is a number.
 */
function SummaryRow({ row }: { row: SupplyRow }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 py-3">
      <dt className="min-w-0 text-sm text-slate-700">{row.label}</dt>

      <dd className="flex min-w-0 flex-1 flex-wrap items-baseline justify-end gap-x-4 gap-y-1 text-right">
        {/* The value column carries a figure, "Not settled" for a real
            disagreement, or a neutral dash where the concept simply
            holds several distinct facts — four excluded addresses are
            not an unsettled quantity, and saying so twice in two
            columns said it wrongly twice. */}
        <span
          className={
            row.stated
              ? "text-sm font-semibold tabular-nums text-slate-900"
              : "text-sm font-medium text-slate-500"
          }
        >
          {row.stated ??
            (row.unsettledKind === "conflicted" ? "Not settled" : "—")}
        </span>

        <span className="w-40 shrink-0 text-xs text-slate-500">
          {row.status}
        </span>
      </dd>

      <p className="w-full text-xs leading-5 text-slate-400">{row.because}</p>
    </div>
  );
}

// ── 3. source detail ────────────────────────────────────────────────

/**
 * One concept's evidence, collapsed.
 *
 * A compact table rather than a card per claim: four excluded-address
 * entries become four rows inside one disclosure, never four primary
 * boxes. Figures are tabular so they align, and each source keeps its
 * own definition, authority, age and caveats on its own row — a caveat
 * belongs to the reading it qualifies.
 */
function SourceGroup({ group }: { group: SupplyGroup }) {
  return (
    <details className="border-t border-slate-100">
      <summary className="cursor-pointer py-3 text-sm font-medium text-slate-700">
        {group.label}
        <span className="ml-2 text-xs font-normal text-slate-400">
          {group.figures.length} reported{" "}
          {group.figures.length === 1 ? "value" : "values"}
        </span>
      </summary>

      <div className="overflow-x-auto pb-4">
        <table className="w-full text-left text-xs">
          <thead className="text-slate-400">
            <tr>
              <th scope="col" className="py-1 pr-4 font-medium">
                Source
              </th>
              <th scope="col" className="py-1 pr-4 text-right font-medium">
                Reported value
              </th>
              <th scope="col" className="py-1 pr-4 font-medium">
                Definition
              </th>
              <th scope="col" className="py-1 font-medium">
                Authority and age
              </th>
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 text-slate-600">
            {group.figures.map((figure, index) => (
              <tr key={`${figure.source}-${figure.stated}-${index}`}>
                <td className="py-2 pr-4 align-top text-slate-800">
                  {figure.source}
                </td>
                <td className="py-2 pr-4 text-right align-top font-medium tabular-nums text-slate-900">
                  {figure.stated}
                </td>
                <td className="py-2 pr-4 align-top">
                  {figure.definedBy} {figure.methodology}
                  {figure.caveats.map((caveat) => (
                    <span key={caveat} className="mt-1 block text-amber-800">
                      {caveat}
                    </span>
                  ))}
                </td>
                <td className="py-2 align-top">
                  {figure.standingStated} · {figure.authorityStated}
                  {figure.age ? (
                    <span className="block text-slate-400">{figure.age}</span>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

// ── the composition ─────────────────────────────────────────────────

export function TokenSupply({ supply }: { supply: SupplyView }) {
  const model = supplyModel(supply);

  if (model.rows.length === 0 && model.groups.length === 0) {
    return (
      <section aria-labelledby="supply-heading">
        <h2 id="supply-heading" className={HEAD}>
          Token supply
        </h2>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
          {model.unavailableBecause ??
            "No supply evidence is held for this asset."}
        </p>
      </section>
    );
  }

  return (
    <section aria-labelledby="supply-heading">
      <h2 id="supply-heading" className={HEAD}>
        Token supply
      </h2>

      {/* Summary wide, unsettled narrow — and the summary is written
          first, so the single mobile column keeps that priority. */}
      <div className="mt-3 grid gap-4 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
        <div className={`${PANEL} px-5 py-3`}>
          <dl className="divide-y divide-slate-100">
            {model.rows.map((row) => (
              <SummaryRow key={row.concept} row={row} />
            ))}
          </dl>
        </div>

        {model.unsettled.length > 0 ? (
          <section
            aria-labelledby="supply-unsettled"
            className="border-l-2 border-slate-200 pl-4 lg:mt-0"
          >
            <h3 id="supply-unsettled" className={HEAD}>
              What remains unsettled
            </h3>

            <ul className="mt-3 space-y-3">
              {model.unsettled.map((item) => (
                <li key={item.stated} className="text-sm leading-6 text-slate-600">
                  {item.stated}
                  {item.consequence ? (
                    <span className="mt-0.5 block text-slate-500">
                      {item.consequence}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>

      {/* Source detail: dividers, not cards. */}
      <div className="mt-6">
        <h3 className={HEAD}>Source detail</h3>

        <div className="mt-1">
          {model.groups.map((group) => (
            <SourceGroup key={group.concept} group={group} />
          ))}
        </div>
      </div>

      {/* The full audit, collapsed. Ten pairwise comparisons are the
          evidence behind the summary above, not the investor's first
          reading — and four provider readings producing six conflict
          cards is a property of pairing, not six findings. */}
      {model.audit.length > 0 ? (
        <details className="mt-4 border-t border-slate-100 pt-3">
          <summary className="cursor-pointer text-xs font-semibold text-slate-500">
            View source-comparison audit ({model.audit.length})
          </summary>

          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400">
                <tr>
                  <th scope="col" className="py-1 pr-4 font-medium">
                    Verdict
                  </th>
                  <th scope="col" className="py-1 pr-4 font-medium">
                    Sources compared
                  </th>
                  <th scope="col" className="py-1 font-medium">
                    Why
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-100 text-slate-600">
                {model.audit.map((item, index) => (
                  <tr key={`${item.leftSource}-${item.rightSource}-${index}`}>
                    <td className="py-2 pr-4 align-top text-slate-800">
                      {item.verdictStated}
                    </td>
                    <td className="py-2 pr-4 align-top">
                      <span className="block tabular-nums">
                        {item.leftSource}: {item.leftStated}
                      </span>
                      <span className="block tabular-nums">
                        {item.rightSource}: {item.rightStated}
                      </span>
                    </td>
                    <td className="py-2 align-top leading-5">{item.because}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </section>
  );
}
