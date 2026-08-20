import { LatestCioReview } from "@/components/executive/LatestCioReview";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { getCycleReview } from "@/lib/api/cycle-review";
import type { CycleReviewFailure } from "@/lib/api/cycle-review";
import { PageIntegrity } from "@/components/system-integrity/PageIntegrity";

export const dynamic = "force-dynamic";

/**
 * Three different failures, worded as three different facts.
 *
 * Calling an unreadable response "backend unreachable" would be a claim
 * about the network made out of a parsing problem — and it would hide
 * the one failure a reader can act on, which is that the two sides
 * disagree about the contract.
 */
export const FAILURE_MEANING: Record<CycleReviewFailure, string> = {
  unreachable:
    "MOVRvest could not reach its own backend, so it cannot read the review history.",
  http_error:
    "MOVRvest reached its backend, but the request for the review history was refused.",
  invalid_contract:
    "MOVRvest reached its backend and received a response it could not read as a cycle review. Rather than guess at the missing parts, it shows nothing.",
};

/**
 * The homepage reads the recorded CIO cycle, and nothing else.
 *
 * It used to call `/brain/` and `/executive/portfolio`. The second of
 * those builds a Brain, runs the executive pipeline and appends journal
 * entries *during the request*, so opening this page acquired evidence
 * and produced decisions — page traffic, rather than the cycle, was the
 * origin of what the investor read.
 *
 * Both are gone from this page. What remains is one read of the
 * append-only cycle store. The portfolio snapshot stays independent on
 * its own page, which is also why a broker failure there can no longer
 * rewrite or recompute anything recorded here.
 */
export default async function HomePage() {
  const result = await getCycleReview();

  return (
    <DashboardLayout>
      <PageIntegrity
        status={result.review ? "live" : "placeholder"}
        endpoint={result.review ? "/cycle/latest" : undefined}
        description={
          result.review
            ? "The latest recorded CIO review, read from the append-only cycle store. This page acquires no evidence, asks no model and makes no decision: it reports what the last recorded review concluded, and when."
            : "Backend unreachable. Nothing is shown in its place: an invented figure on an investment surface would read as a measurement."
        }
      />

      <main className="mx-auto w-full max-w-[1600px] px-5 py-8 sm:px-8 lg:px-10 lg:py-12">
        {result.review ? (
          <LatestCioReview review={result.review} />
        ) : (
          <section className="rounded-[28px] border border-amber-200 bg-amber-50 px-8 py-10">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-700">
              Overview
            </p>

            <h1 className="mt-3 text-3xl font-semibold tracking-[-0.035em] text-amber-950">
              Latest CIO review unavailable
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-6 text-amber-900">
              {FAILURE_MEANING[result.failure ?? "unreachable"]} Nothing is
              shown in its place: no demo figures stand in for real ones, and no
              earlier review is presented as though it were the latest.
            </p>

            <p className="mt-6 text-sm text-amber-900">
              Tried:
              <code className="ml-2 rounded bg-white/70 px-1.5 py-0.5">
                {result.backendUrl}
              </code>
            </p>

            {result.detail ? (
              <details className="mt-4 text-sm text-amber-900">
                <summary className="cursor-pointer font-semibold">
                  Connection details
                </summary>

                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs leading-5">
                  {result.detail}
                </pre>
              </details>
            ) : null}
          </section>
        )}
      </main>
    </DashboardLayout>
  );
}
