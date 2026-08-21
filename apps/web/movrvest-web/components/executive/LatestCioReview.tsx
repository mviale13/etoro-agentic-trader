import {
  HoldingsTable,
  Opportunities,
  PortfolioSnapshot,
  StrategyCard,
} from "@/components/executive/HomeSections";
import type {
  CycleCourse,
  CycleReview,
  LastKnownCycle,
} from "@/lib/api/cycle-review";

/**
 * The latest recorded CIO review.
 *
 * Everything shown is carried from the cycle record. This component
 * chooses layout and plain wording; it never decides what happened.
 * Four distinctions it must not blur, each one a way a page could lie:
 *
 * - a failed or interrupted review is **not** a quiet day;
 * - a first review is **not** an unchanged one;
 * - an incomplete history permits **no** movement claim;
 * - an evidence refusal says nothing about a company's quality.
 */

function when(value: string | null): string {
  if (!value) {
    return "an unstated time";
  }

  const parsed = new Date(value);

  return Number.isNaN(parsed.getTime())
    ? "an unstated time"
    : parsed.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
      });
}

export const EXECUTION_HEADLINE: Record<CycleReview["execution"], string> = {
  none_recorded: "No review has been run yet",
  interrupted: "The last review started and did not finish",
  failed: "The last review could not complete",
  partial: "The last review completed only in part",
  complete: "The last review completed",
};

/**
 * The same five states, worded for an incomplete history.
 *
 * When part of the record could not be read, the newest decoded record
 * is only the newest **readable** record — an unreadable or unsupported
 * line may be newer still. So nothing here may say "the last review".
 */
export const READABLE_HEADLINE: Record<CycleReview["execution"], string> = {
  none_recorded: "No readable review was found",
  interrupted: "The latest readable review started and did not finish",
  failed: "The latest readable review could not complete",
  partial: "The latest readable review completed only in part",
  complete: "The latest readable review completed",
};

export const INCOMPLETE_HISTORY =
  "Part of the review history could not be read, so this is the latest " +
  "review MOVRvest can read — not necessarily the latest one attempted. " +
  "A newer review may exist in the unreadable part of the record.";

const EXECUTION_MEANING: Record<CycleReview["execution"], string> = {
  none_recorded:
    "MOVRvest has not yet recorded a review of your account. Nothing below stands in for one.",
  interrupted:
    "It stopped part-way through, so it reached no conclusion. This is not a quiet day — it is a review that did not happen.",
  failed:
    "A step it needs did not run, so no course was produced. This says nothing about your holdings; it says the review failed.",
  partial:
    "Some of what it needs did not run. What it did conclude is below, and the part that failed is named.",
  complete: "Every step it needs ran.",
};

function ComparisonNote({ review }: { review: CycleReview }) {
  if (!review.streamComplete) {
    return (
      <p className="text-sm leading-6 text-slate-700">
        No comparison with a previous review is claimed here — not even that
        nothing changed — because the history it would rest on is incomplete.
      </p>
    );
  }

  if (review.comparisonOutcome === "initial_baseline") {
    return (
      <p className="text-sm leading-6 text-slate-700">
        This is the first recorded review, so there is nothing to compare it
        with. That is different from finding no changes.
      </p>
    );
  }

  if (review.comparisonOutcome === "refused") {
    return (
      <p className="text-sm leading-6 text-slate-700">
        No comparison with a previous review was made: {review.comparisonBecause}
        . Nothing is claimed about what moved.
      </p>
    );
  }

  if (review.comparisonOutcome === "compared") {
    return (
      <p className="text-sm leading-6 text-slate-700">
        Compared against the previous recorded review.
      </p>
    );
  }

  return null;
}

function Envelope({ course }: { course: CycleCourse }) {
  const envelope = course.envelope;

  if (!envelope) {
    return null;
  }

  return (
    <div className="mt-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
      {/* The domain's own sentence, rendered as written. */}
      <p className="text-sm leading-6 text-slate-800">{envelope.stated}</p>

      {envelope.namedGaps.length > 0 ? (
        <p className="mt-2 text-xs leading-5 text-slate-600">
          What limits this consideration — and it limits the action, not the
          company: {envelope.namedGaps.join("; ")}
        </p>
      ) : null}

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {envelope.liquidity}
      </p>
    </div>
  );
}

function Course({ course }: { course: CycleCourse }) {
  return (
    <li className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-base font-semibold text-slate-950">
          {course.symbol}
        </span>

        <span className="text-xs uppercase tracking-[0.18em] text-slate-500">
          {course.disposition}
        </span>
      </div>

      {course.actionStatement ? (
        <p className="mt-2 text-sm leading-6 text-slate-800">
          {course.actionStatement}
        </p>
      ) : (
        <p className="mt-2 text-sm leading-6 text-slate-600">
          This review produced no course for {course.symbol}.
        </p>
      )}

      {course.actionBecause ? (
        <p className="mt-2 text-sm leading-6 text-slate-600">
          {course.actionBecause}
        </p>
      ) : null}

      {course.asksForSomething ? (
        <p className="mt-2 text-xs leading-5 text-slate-500">
          This is a course to consider, not an instruction, and nothing is
          placed for you.
        </p>
      ) : null}

      <Envelope course={course} />

      {course.evidenceAsOf ? (
        <p className="mt-3 text-xs text-slate-500">
          Evidence as of {course.evidenceAsOf}
        </p>
      ) : null}
    </li>
  );
}

function LastKnown({
  lastKnown,
  streamComplete,
}: {
  lastKnown: LastKnownCycle;
  streamComplete: boolean;
}) {
  return (
    <section className="mt-8 rounded-3xl border border-slate-300 bg-slate-50 p-6">
      <h3 className="text-sm font-semibold text-slate-900">
        {streamComplete
          ? "Last completed review"
          : "Latest readable completed review"}{" "}
        — {when(lastKnown.finishedAt)}
      </h3>

      <p className="mt-2 text-sm leading-6 text-slate-700">
        This is what that review concluded. It is shown with its date because it
        is not current: the attempt described above is the more recent one.
        {streamComplete
          ? ""
          : " Because the history is incomplete, it is the most recent completed review MOVRvest can read, not necessarily the most recent one that ran."}
      </p>

      <ul className="mt-4 grid gap-3">
        {lastKnown.courses.map((course) => (
          <Course course={course} key={`${lastKnown.cycleId}-${course.symbol}`} />
        ))}
      </ul>
    </section>
  );
}

export function LatestCioReview({ review }: { review: CycleReview }) {
  const ran =
    review.execution === "none_recorded"
      ? null
      : (review.finishedAt ?? review.startedAt);

  const failedStages = review.stages.filter((stage) => stage.outcome !== "ran");

  const headline = review.streamComplete
    ? EXECUTION_HEADLINE[review.execution]
    : READABLE_HEADLINE[review.execution];

  return (
    <div className="grid gap-6">
      {/*
        The review's own status, as a compact strip rather than a hero.
        It cannot be dropped — a failed or interrupted review must never
        read as a quiet one — but it is no longer the biggest thing on
        the page.
      */}
      <section className="rounded-3xl border border-slate-200 bg-white px-6 py-4">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <p className="text-sm font-semibold text-slate-900">{headline}</p>

          {ran ? <p className="text-xs text-slate-500">{when(ran)}</p> : null}
        </div>

        <p className="mt-1 text-sm leading-6 text-slate-600">
          {EXECUTION_MEANING[review.execution]}
        </p>

        {review.streamComplete ? null : (
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {INCOMPLETE_HISTORY}
          </p>
        )}

        <div className="mt-2 text-sm leading-6 text-slate-600">
          <ComparisonNote review={review} />
        </div>

        {review.noActionSuggested ? (
          <p className="mt-2 text-sm leading-6 text-slate-800">
            {review.noActionSuggested} This describes what the review found, and
            is not an assessment that your portfolio is safe.
          </p>
        ) : null}

        {failedStages.length > 0 ? (
          <ul className="mt-3 grid gap-2">
            {failedStages.map((stage) => (
              <li
                className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-2.5 text-sm leading-6 text-amber-900"
                key={stage.name}
              >
                {stage.because || `The ${stage.name} step did not run.`}
              </li>
            ))}
          </ul>
        ) : null}

        {review.refusals.length > 0 ? (
          <div className="mt-3">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              What could not be read
            </p>

            <ul className="mt-1 grid gap-1">
              {review.refusals.map((item) => (
                <li className="text-sm leading-6 text-slate-700" key={item}>
                  {item}
                </li>
              ))}
            </ul>

            <p className="mt-1 text-xs leading-5 text-slate-500">
              Each limits what this review could say. None is a finding about
              the company.
            </p>
          </div>
        ) : null}
      </section>

      <PortfolioSnapshot portfolio={review.portfolio} />

      <HoldingsTable review={review} />

      <Opportunities
        candidates={review.candidates}
        ranked={review.candidatesRanked}
      />

      <StrategyCard portfolio={review.portfolio} />

      {review.lastKnown ? (
        <LastKnown
          lastKnown={review.lastKnown}
          streamComplete={review.streamComplete}
        />
      ) : null}
    </div>
  );
}
