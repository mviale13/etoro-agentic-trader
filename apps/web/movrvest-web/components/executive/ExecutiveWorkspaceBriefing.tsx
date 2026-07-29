import Link from "next/link";
import {
  ArrowRight,
  Building2,
  ChartNoAxesCombined,
  CircleAlert,
  CircleCheck,
  Clock3,
  Landmark,
  Newspaper,
} from "lucide-react";

import type {
  ChangeSeverity,
  ExecutiveWorkspaceViewModel,
  PriorityUrgency,
} from "@/lib/view-models/executive-workspace";

interface ExecutiveWorkspaceBriefingProps {
  workspace: ExecutiveWorkspaceViewModel;
}

const changePresentation: Record<
  ChangeSeverity,
  {
    icon: typeof CircleAlert;
    iconClassName: string;
    label: string;
  }
> = {
  important: {
    icon: CircleAlert,
    iconClassName: "text-rose-600",
    label: "Important",
  },
  attention: {
    icon: Clock3,
    iconClassName: "text-amber-600",
    label: "Attention",
  },
  information: {
    icon: CircleCheck,
    iconClassName: "text-sky-600",
    label: "Update",
  },
};

const priorityPresentation: Record<
  PriorityUrgency,
  {
    markerClassName: string;
    label: string;
  }
> = {
  now: {
    markerClassName: "bg-rose-500",
    label: "Review now",
  },
  today: {
    markerClassName: "bg-amber-500",
    label: "Review today",
  },
  monitor: {
    markerClassName: "bg-sky-500",
    label: "Monitor",
  },
};

function ReviewMetric({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof Building2;
  value: number;
  label: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600">
        <Icon aria-hidden="true" className="size-4" />
      </span>

      <div>
        <p className="text-sm font-semibold text-slate-950">
          {value.toLocaleString("en-US")}
        </p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  );
}

export function ExecutiveWorkspaceBriefing({
  workspace,
}: ExecutiveWorkspaceBriefingProps) {
  return (
    <div className="space-y-14">
      <section
        aria-labelledby="executive-workspace-heading"
        className="border-b border-slate-200 pb-10"
      >
        <p className="text-sm font-medium text-slate-500">
          Executive Workspace · {workspace.lastReviewedAt}
        </p>

        <div className="mt-5 grid gap-8 xl:grid-cols-[minmax(0,1fr)_auto] xl:items-end">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-slate-500">
              Latest CIO review
            </p>

            <h1
              id="executive-workspace-heading"
              className="mt-3 max-w-4xl text-4xl font-semibold tracking-[-0.045em] text-slate-950 sm:text-5xl"
            >
              {workspace.headline}
            </h1>

            <p className="mt-5 max-w-4xl text-lg leading-8 text-slate-600">
              {workspace.summary}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-x-8 gap-y-5 sm:grid-cols-4 xl:grid-cols-2">
            <ReviewMetric
              icon={Building2}
              value={workspace.reviewed.portfolioHoldings}
              label="Portfolio holdings"
            />
            <ReviewMetric
              icon={ChartNoAxesCombined}
              value={workspace.reviewed.companies}
              label="Companies reviewed"
            />
            <ReviewMetric
              icon={Newspaper}
              value={workspace.reviewed.marketEvents}
              label="Market events"
            />
            <ReviewMetric
              icon={Landmark}
              value={workspace.reviewed.macroIndicators}
              label="Macro indicators"
            />
          </div>
        </div>
      </section>

      <section aria-labelledby="changes-heading">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Since your last visit
            </p>
            <h2
              id="changes-heading"
              className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-950"
            >
              What changed
            </h2>
          </div>

          <p className="max-w-lg text-sm leading-6 text-slate-500">
            Changes are ranked by relevance to your portfolio, investment policy
            and active research.
          </p>
        </div>

        <div className="mt-7 divide-y divide-slate-200 border-y border-slate-200">
          {workspace.changes.map((change) => {
            const presentation = changePresentation[change.severity];
            const Icon = presentation.icon;

            const content = (
              <div className="group grid gap-4 py-5 sm:grid-cols-[24px_minmax(0,1fr)_auto] sm:items-start">
                <Icon
                  aria-hidden="true"
                  className={`mt-0.5 size-5 ${presentation.iconClassName}`}
                />

                <div>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <h3 className="font-semibold text-slate-950">
                      {change.title}
                    </h3>
                    <span className="text-xs font-medium text-slate-400">
                      {presentation.label}
                    </span>
                  </div>

                  <p className="mt-1 text-sm leading-6 text-slate-700">
                    {change.detail}
                  </p>

                  {change.context ? (
                    <p className="mt-1 text-sm leading-6 text-slate-500">
                      {change.context}
                    </p>
                  ) : null}
                </div>

                {change.href ? (
                  <ArrowRight
                    aria-hidden="true"
                    className="hidden size-4 text-slate-400 transition-transform group-hover:translate-x-1 sm:block"
                  />
                ) : null}
              </div>
            );

            return change.href ? (
              <Link key={change.id} href={change.href} className="block">
                {content}
              </Link>
            ) : (
              <div key={change.id}>{content}</div>
            );
          })}
        </div>
      </section>

      <section aria-labelledby="priorities-heading">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Artificial CIO
          </p>
          <h2
            id="priorities-heading"
            className="mt-2 text-3xl font-semibold tracking-[-0.035em] text-slate-950"
          >
            Executive actions
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
            These are attention items, not automatic trades. You remain in
            control of every investment decision.
          </p>
        </div>

        <div className="mt-7 grid gap-4 xl:grid-cols-3">
          {workspace.priorities.map((priority) => {
            const presentation = priorityPresentation[priority.urgency];

            const content = (
              <article className="group h-full rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_18px_55px_-40px_rgba(15,23,42,0.5)] transition hover:-translate-y-0.5 hover:border-slate-300">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-2.5">
                    <span
                      aria-hidden="true"
                      className={`size-2 rounded-full ${presentation.markerClassName}`}
                    />
                    <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                      {presentation.label}
                    </span>
                  </div>

                  {priority.estimatedMinutes ? (
                    <span className="text-xs font-medium text-slate-400">
                      {priority.estimatedMinutes} min
                    </span>
                  ) : null}
                </div>

                <h3 className="mt-5 text-xl font-semibold tracking-tight text-slate-950">
                  {priority.title}
                </h3>

                <p className="mt-3 text-sm leading-6 text-slate-600">
                  {priority.rationale}
                </p>

                {priority.href ? (
                  <div className="mt-7 flex items-center gap-2 text-sm font-semibold text-slate-950">
                    Open action
                    <ArrowRight
                      aria-hidden="true"
                      className="size-4 transition-transform group-hover:translate-x-1"
                    />
                  </div>
                ) : null}
              </article>
            );

            return priority.href ? (
              <Link key={priority.id} href={priority.href}>
                {content}
              </Link>
            ) : (
              <div key={priority.id}>{content}</div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
