import Link from "next/link";
import {
  ArrowRight,
  BriefcaseBusiness,
  CircleAlert,
  CircleCheck,
  Clock3,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { StatusPill } from "@/components/ui/StatusPill";
import type {
  ChangeSeverity,
  ExecutiveWorkspaceViewModel,
  PortfolioSnapshotViewModel,
  PriorityUrgency,
} from "@/lib/view-models/executive-workspace";

interface ExecutiveWorkspaceBriefingProps {
  workspace: ExecutiveWorkspaceViewModel;
  dataSource?: "backend" | "fallback";
}

const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

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

function SnapshotMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail?: string;
}) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-500">
        {label}
      </dt>

      <dd className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">
        {value}
      </dd>

      {detail ? (
        <p className="mt-1 text-xs leading-5 text-slate-500">{detail}</p>
      ) : null}
    </div>
  );
}

function DataSourceBadge({
  dataSource,
}: {
  dataSource: "backend" | "fallback";
}) {
  const isBackend = dataSource === "backend";

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold ${
        isBackend
          ? "border-emerald-200 bg-emerald-50 text-emerald-700"
          : "border-amber-200 bg-amber-50 text-amber-700"
      }`}
    >
      <span
        aria-hidden="true"
        className={`size-1.5 rounded-full ${
          isBackend ? "bg-emerald-500" : "bg-amber-500"
        }`}
      />

      {isBackend ? "Live backend" : "Demo fallback"}
    </div>
  );
}

function PortfolioSnapshot({
  portfolio,
  reviewedAt,
  dataSource,
}: {
  portfolio: PortfolioSnapshotViewModel;
  reviewedAt: string;
  dataSource: "backend" | "fallback";
}) {
  const cashRatio =
    portfolio.totalEquity > 0
      ? Math.round((portfolio.availableCash / portfolio.totalEquity) * 100)
      : 0;

  const investedDetail =
    portfolio.unrealizedProfitLoss === null
      ? "Unrealized P&L not reported"
      : `${
          portfolio.unrealizedProfitLoss > 0 ? "+" : ""
        }${currencyFormatter.format(
          portfolio.unrealizedProfitLoss,
        )} unrealized P&L`;

  const positionsDetail =
    portfolio.pendingOrders === null
      ? "Open positions"
      : `${portfolio.pendingOrders} pending orders`;

  return (
    <section aria-labelledby="portfolio-snapshot-heading">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Executive Workspace · {reviewedAt}
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h1
              id="portfolio-snapshot-heading"
              className="text-4xl font-semibold tracking-[-0.045em] text-slate-950 sm:text-5xl"
            >
              Portfolio snapshot
            </h1>

            {/* Real account figures, unless the backend was unreachable and
                the demo workspace is standing in. */}
            {dataSource === "backend" ? (
              <StatusPill status="live" label="Live account" />
            ) : (
              <StatusPill status="placeholder" label="Demo data" />
            )}
          </div>
        </div>

        <Link
          href="/portfolio"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-950"
        >
          Open portfolio
          <ArrowRight aria-hidden="true" className="size-4" />
        </Link>
      </div>

      <div className="mt-8 overflow-hidden rounded-[28px] border border-slate-200 bg-white shadow-[0_20px_70px_-48px_rgba(15,23,42,0.55)]">
        <dl className="grid gap-px bg-slate-200 sm:grid-cols-2 xl:grid-cols-5">
          <div className="bg-white p-6">
            <SnapshotMetric
              label="Total equity"
              value={currencyFormatter.format(portfolio.totalEquity)}
              detail="Current account value"
            />
          </div>

          <div className="bg-white p-6">
            <SnapshotMetric
              label="Available cash"
              value={currencyFormatter.format(portfolio.availableCash)}
              detail={`${cashRatio}% of portfolio`}
            />
          </div>

          <div className="bg-white p-6">
            <SnapshotMetric
              label="Invested"
              value={currencyFormatter.format(portfolio.invested)}
              detail={investedDetail}
            />
          </div>

          <div className="bg-white p-6">
            <SnapshotMetric
              label="Positions"
              value={portfolio.openPositions.toString()}
              detail={positionsDetail}
            />
          </div>

          <div className="bg-white p-6">
            <SnapshotMetric
              label="Portfolio health"
              value={`${portfolio.healthScore} / 100`}
              detail={portfolio.healthLabel}
            />
          </div>
        </dl>

        <div className="grid gap-5 border-t border-slate-200 px-6 py-5 text-sm sm:grid-cols-3">
          <div className="flex items-center gap-3">
            <WalletCards aria-hidden="true" className="size-4 text-slate-400" />
            <span className="text-slate-500">Liquidity</span>
            <span className="ml-auto font-semibold text-slate-950">
              {currencyFormatter.format(portfolio.availableCash)}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <ShieldCheck aria-hidden="true" className="size-4 text-slate-400" />
            <span className="text-slate-500">Risk</span>
            <span className="ml-auto font-semibold text-slate-950">
              {portfolio.riskLevel}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <BriefcaseBusiness
              aria-hidden="true"
              className="size-4 text-slate-400"
            />
            <span className="text-slate-500">Diversification</span>
            <span className="ml-auto font-semibold text-slate-950">
              {portfolio.diversification}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}

export function ExecutiveWorkspaceBriefing({
  workspace,
  dataSource = "fallback",
}: ExecutiveWorkspaceBriefingProps) {
  return (
    <div className="space-y-16">
      <div>
        <div className="mb-4 flex justify-end">
          <DataSourceBadge dataSource={dataSource} />
        </div>

        <PortfolioSnapshot
          portfolio={workspace.portfolio}
          reviewedAt={workspace.lastReviewedAt}
          dataSource={dataSource}
        />
      </div>

      <section aria-labelledby="changes-heading">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
              Since your last visit
            </p>

            <div className="mt-2 flex items-center gap-3">

              <h2
                id="changes-heading"
                className="text-3xl font-semibold tracking-[-0.035em] text-slate-950"
              >
                What changed
              </h2>

              {/* Decision changes and market movements — mood, volatility
                  and sentiment — are recorded and reported. Individual
                  instrument moves are not measured yet, so the feed is
                  genuine but partial. */}
              {dataSource === "backend" ? (
                <StatusPill status="partial" label="Decisions & market moves" />
              ) : (
                <StatusPill status="placeholder" label="Demo data" />
              )}

            </div>
          </div>

          <p className="max-w-lg text-sm leading-6 text-slate-500">
            Every decision the Artificial CIO changed about a holding, and how
            the market moved — mood, volatility and sentiment — newest first.
            Individual instrument moves are not tracked here yet.
          </p>
        </div>

        <div className="mt-7 divide-y divide-slate-200 border-y border-slate-200">
          {workspace.changes.length === 0 ? (
            <p className="py-8 text-sm leading-6 text-slate-500">
              The Artificial CIO has not changed its decision on any holding.
              This fills in when one of them moves.
            </p>
          ) : null}

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

      <section aria-labelledby="actions-heading">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">
            Artificial CIO
          </p>

          <div className="mt-2 flex items-center gap-3">
            <h2
              id="actions-heading"
              className="text-3xl font-semibold tracking-[-0.035em] text-slate-950"
            >
              {workspace.priorities.length === 0
                ? "No executive actions"
                : `${workspace.priorities.length} executive actions`}
            </h2>

            {/* Decisions come from the Artificial CIO, which now remembers
                what it decided before. Behavioural consistency still needs a
                record of the investor's own actions, so this is genuine but
                incomplete reasoning. */}
            {dataSource === "backend" ? (
              <StatusPill status="partial" label="Artificial CIO" />
            ) : (
              <StatusPill status="placeholder" label="Demo data" />
            )}
          </div>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-500">
            These are attention items, not automatic trades. You remain in
            control of every investment decision.
          </p>
        </div>

        {workspace.brief ? (
          <article className="mt-7 rounded-[24px] border border-slate-200 bg-slate-50 p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="text-xl font-semibold tracking-tight text-slate-950">
                {workspace.brief.headline}
              </h3>

              {/* Committee agreement across the whole briefing, not the
                  CIO's conviction — that is held in a decision about one
                  security, and is shown per case below. Null where no
                  committee could form a view, which is not the same as
                  their having disagreed. */}
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                {workspace.brief.confidence === null
                  ? "Committee agreement not measured"
                  : `${Math.round(workspace.brief.confidence * 100)}% committee agreement`}
              </span>
            </div>

            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
              {workspace.brief.summary}
            </p>
          </article>
        ) : null}

        <div className="mt-7 grid gap-4 xl:grid-cols-3">
          {workspace.priorities.map((priority, index) => {
            const presentation = priorityPresentation[priority.urgency];

            const content = (
              <article className="group h-full rounded-[24px] border border-slate-200 bg-white p-6 shadow-[0_18px_55px_-40px_rgba(15,23,42,0.5)] transition hover:-translate-y-0.5 hover:border-slate-300">
                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-semibold text-slate-400">
                      {String(index + 1).padStart(2, "0")}
                    </span>

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
