import {
  ChartPie,
  LineChart,
  ShieldCheck,
  TrendingDown,
  Wallet,
} from "lucide-react";

import { StatusPill } from "@/components/ui/StatusPill";
import type { PortfolioRisk } from "@/lib/api/portfolio";

type ExecutivePortfolioAssessmentProps = {
  risk: PortfolioRisk | null;
};

type ScoreRowProps = {
  label: string;
  score: number | null;
  description: string;
  icon: typeof Wallet;
};

/**
 * One risk component, as five segments.
 *
 * The bars are presentation; the score they fill is measured in the Brain
 * and arrives ready. This component used to derive all four scores from
 * the cash percentage with hardcoded ladders, which put invented risk on
 * the page under the same heading as the real figures.
 */
function ScoreRow({ label, score, description, icon: Icon }: ScoreRowProps) {
  const filled = score === null ? 0 : Math.ceil(score * 5);

  return (
    <div className="flex flex-col gap-3 border-b border-slate-100 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <Icon aria-hidden="true" className="h-5 w-5 shrink-0 text-slate-500" />

        <div>
          <span className="font-medium text-slate-900">{label}</span>

          <p className="text-sm leading-6 text-slate-500">{description}</p>
        </div>
      </div>

      {score === null ? (
        <span className="shrink-0 text-sm font-medium text-slate-400">
          Not measured
        </span>
      ) : (
        <div
          aria-label={`${label}: ${filled} out of 5`}
          className="flex shrink-0 gap-1"
          role="img"
        >
          {Array.from({ length: 5 }, (_, index) => (
            <span
              className={`h-2.5 w-8 rounded-full ${
                index < filled ? "bg-slate-900" : "bg-slate-200"
              }`}
              key={`${label}-${index}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export function ExecutivePortfolioAssessment({
  risk,
}: ExecutivePortfolioAssessmentProps) {
  const level = risk?.level?.replace("_", " ") ?? null;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <ShieldCheck aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              How this account can lose money
            </h2>

            <p className="mt-1 text-sm leading-6 text-slate-500">
              {level
                ? `Overall risk reads ${level}, across the four components below.`
                : "Overall risk is withheld while any component below is unmeasured."}
            </p>
          </div>
        </div>

        {risk ? (
          <StatusPill
            status={risk.unmeasured.length === 0 ? "live" : "partial"}
            label={
              risk.unmeasured.length === 0
                ? "Fully measured"
                : `${risk.unmeasured.length} unmeasured`
            }
          />
        ) : (
          <StatusPill status="partial" label="Risk unavailable" />
        )}
      </div>

      <div className="mt-6">
        <ScoreRow
          description="How violently the market this account is exposed to has moved"
          icon={LineChart}
          label="Market"
          score={risk?.market ?? null}
        />

        <ScoreRow
          description="The deepest fall the account took, against the limit the investor set"
          icon={TrendingDown}
          label="Drawdown"
          score={risk?.drawdown ?? null}
        />

        <ScoreRow
          description="How much of the account sits in its largest holding"
          icon={ChartPie}
          label="Concentration"
          score={risk?.concentration ?? null}
        />

        <ScoreRow
          description="How little cash is left to act with"
          icon={Wallet}
          label="Liquidity"
          score={risk?.liquidity ?? null}
        />
      </div>

      {risk && risk.evidence.length > 0 ? (
        <div className="mt-6 space-y-4 rounded-2xl border border-slate-200 bg-slate-50 p-5">
          {risk.evidence.map((item) => (
            <div key={item.statement}>
              <p className="leading-7 text-slate-700">{item.statement}</p>

              {item.source ? (
                <p className="mt-1 text-sm text-slate-500">{item.source}</p>
              ) : null}
            </div>
          ))}
        </div>
      ) : null}

      {risk && risk.unmeasured.length > 0 ? (
        <ul className="mt-4 space-y-1 text-sm text-slate-500">
          {risk.unmeasured.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
