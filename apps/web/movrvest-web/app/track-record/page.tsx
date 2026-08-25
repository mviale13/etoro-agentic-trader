import { Database, History, Scale, Timer } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { PageMain } from "@/components/layout/PageMain";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";
import { StatusPill } from "@/components/ui/StatusPill";
import {
  getTrackRecord,
  type TrackRecordOutcome,
  type TrackRecordViewModel,
} from "@/lib/api/track-record";

export const dynamic = "force-dynamic";

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <span className="block text-sm font-medium text-slate-500">{label}</span>

      <strong className="mt-2 block text-3xl font-semibold tracking-tight text-slate-950">
        {value}
      </strong>
    </div>
  );
}

/**
 * The hit rate, or the honest reason there is not one.
 *
 * The absence is not a modest zero. Below the backend's minimum the
 * figure would move several points per decision — arithmetic on a
 * handful of days dressed as a measurement of judgement.
 */
function HitRate({ record }: { record: TrackRecordViewModel }) {
  return (
    <section className="rounded-3xl border border-slate-200 bg-slate-950 p-6 text-white sm:p-8">
      <div className="flex items-start gap-4">
        <Scale
          aria-hidden="true"
          className="mt-1 h-5 w-5 shrink-0 text-slate-300"
        />

        <div>
          <p className="text-sm font-medium text-slate-400">Hit rate</p>

          {record.hitRate === null ? (
            <>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                Not yet a rate
              </h2>

              <p className="mt-3 max-w-2xl leading-7 text-slate-300">
                {record.minimumCalls} measured calls are needed before a hit
                rate means anything, and {record.calls}{" "}
                {record.calls === 1 ? "has" : "have"} been measured. Until
                then the honest figure is no figure: a rate over a handful of
                decisions moves several points per decision and reads as a
                skill it cannot evidence.
              </p>
            </>
          ) : (
            <>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                {(record.hitRate * 100).toFixed(0)}% of calls moved as decided
              </h2>

              <p className="mt-3 max-w-2xl leading-7 text-slate-300">
                {record.agreed} of {record.calls} measured calls have so far
                moved the way the decision implied. This measures observed
                windows, not the thesis: the investor&apos;s horizon is
                years, and these are its first months.
              </p>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

function OutcomeRow({ outcome }: { outcome: TrackRecordOutcome }) {
  const up = outcome.changePct > 0;

  return (
    <tr className="border-b border-slate-100 last:border-0">
      <td className="py-3 pr-4">
        <p className="font-medium text-slate-900">{outcome.symbol}</p>

        <p className="text-sm text-slate-500">
          {outcome.state} · decided {outcome.decidedOn}
        </p>
      </td>

      <td
        className={`py-3 pr-4 text-right font-medium tabular-nums ${
          up ? "text-emerald-700" : "text-rose-700"
        }`}
      >
        {up ? "+" : ""}
        {outcome.changePct.toFixed(1)}%
      </td>

      <td className="py-3 pr-4 text-right tabular-nums text-slate-600">
        {outcome.daysElapsed}d
      </td>

      <td className="py-3 text-right">
        <span
          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
            outcome.agreed === null
              ? "bg-slate-100 text-slate-500"
              : outcome.agreed
                ? "bg-emerald-50 text-emerald-800"
                : "bg-rose-50 text-rose-800"
          }`}
        >
          {outcome.verdict}
        </span>
      </td>
    </tr>
  );
}

function TrackRecordContent({ record }: { record: TrackRecordViewModel }) {
  return (
    <>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Decisions recorded" value={String(record.recorded)} />
        <Stat label="Old enough to measure" value={String(record.measured)} />
        <Stat label="Of those, calls" value={String(record.calls)} />
        <Stat label="Not yet measurable" value={String(record.unscoredTotal)} />
      </section>

      <div className="mt-6">
        <HitRate record={record} />
      </div>

      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <History aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Measured decisions
            </h2>

            <p className="mt-1 text-sm leading-6 text-slate-500">
              Every decision that has stood long enough to measure, best move
              first. &quot;Not a call&quot; marks decisions that implied
              nothing, or moves too small to be evidence for anybody.
            </p>
          </div>
        </div>

        {record.outcomes.length === 0 ? (
          <p className="mt-6 leading-7 text-slate-600">
            No recorded decision is old enough to measure yet. That is the
            whole finding — the platform is not withholding results, it does
            not have any.
          </p>
        ) : (
          <div className="mt-6 overflow-x-auto">
            <table className="w-full min-w-[32rem] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500">
                  <th className="pb-3 pr-4 font-medium">Decision</th>
                  <th className="pb-3 pr-4 text-right font-medium">
                    Move since
                  </th>
                  <th className="pb-3 pr-4 text-right font-medium">Standing</th>
                  <th className="pb-3 text-right font-medium">So far</th>
                </tr>
              </thead>

              <tbody>
                {record.outcomes.map((outcome) => (
                  <OutcomeRow
                    key={`${outcome.symbol}-${outcome.decidedOn}`}
                    outcome={outcome}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}

        {record.outcomes.length > 0 ? (
          <p className="mt-5 text-xs text-slate-500">
            {record.outcomes[0].reading}. A month of price action is the
            beginning of a story, not a verdict on a thesis.
          </p>
        ) : null}
      </section>

      {record.unscoredReasons.length > 0 ? (
        <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
              <Timer aria-hidden="true" className="h-5 w-5" />
            </div>

            <div>
              <h2 className="text-xl font-semibold tracking-tight text-slate-950">
                Not yet measurable
              </h2>

              <p className="mt-1 text-sm leading-6 text-slate-500">
                Carried, not dropped: a track record built only from the
                decisions that happened to be measurable would describe a
                different platform from the one that made them.
              </p>
            </div>
          </div>

          <ul className="mt-6 space-y-2">
            {record.unscoredReasons.map((item) => (
              <li
                className="flex items-baseline gap-3 text-sm leading-6 text-slate-700"
                key={item.reason}
              >
                <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold tabular-nums text-slate-600">
                  {item.count}×
                </span>

                <span>{item.reason}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </>
  );
}

export default async function TrackRecordPage() {
  const result = await getTrackRecord();

  return (
    <DashboardLayout>
      <PageIntegrity
        status={result.record ? "live" : "placeholder"}
        endpoint={result.record ? "/track-record/" : undefined}
        description={
          result.record
            ? "Recorded decisions measured against Yahoo Finance closes. Outcomes younger than the maturity window are reported as unmeasurable, never estimated."
            : "Backend unreachable, no track record shown."
        }
      />

      <PageMain>
        <header className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              Track Record
            </p>

            <div className="mt-3 flex flex-wrap items-center gap-3">
              <h1 className="text-4xl font-semibold tracking-tight text-slate-950 sm:text-5xl">
                What the decisions did next
              </h1>

              {result.record ? (
                <StatusPill status="live" label="Measured" />
              ) : (
                <StatusPill status="placeholder" label="Unavailable" />
              )}
            </div>

            <p className="mt-4 max-w-3xl text-lg leading-8 text-slate-600">
              Every decision the Artificial CIO records is measured against
              what the market did afterwards — once it has stood long enough
              for the move to say anything at all.
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Database aria-hidden="true" className="h-4 w-4" />

            {result.record ? "Decision journal + Yahoo Finance" : "Backend unavailable"}
          </div>
        </header>

        {result.record ? (
          <TrackRecordContent record={result.record} />
        ) : (
          <section className="rounded-3xl border border-amber-200 bg-amber-50 p-6 text-amber-950">
            <h2 className="font-semibold">Unable to load the track record</h2>

            <p className="mt-2 leading-7">
              Start the MOVRvest backend and reload this page.
            </p>

            <details className="mt-4 text-sm">
              <summary className="cursor-pointer font-medium">
                Technical details
              </summary>

              <p className="mt-2 break-words font-mono text-xs">
                {result.backendUrl}
              </p>

              {result.error ? (
                <p className="mt-2 break-words font-mono text-xs">
                  {result.error}
                </p>
              ) : null}
            </details>
          </section>
        )}
      </PageMain>
    </DashboardLayout>
  );
}
