import {
  ChartPie,
  ShieldCheck,
  TrendingUp,
  Wallet,
} from "lucide-react";

type ExecutivePortfolioAssessmentProps = {
  liquidity: number;
  positions: number;
};

type ScoreRowProps = {
  label: string;
  score: number;
  icon: typeof Wallet;
};

function scoreSegments(score: number): boolean[] {
  return Array.from({ length: 5 }, (_, index) => index < score);
}

function ScoreRow({
  label,
  score,
  icon: Icon,
}: ScoreRowProps) {
  return (
    <div className="flex flex-col gap-3 border-b border-slate-100 py-4 last:border-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <Icon
          aria-hidden="true"
          className="h-5 w-5 text-slate-500"
        />

        <span className="font-medium text-slate-900">
          {label}
        </span>
      </div>

      <div
        aria-label={`${label}: ${score} out of 5`}
        className="flex gap-1"
        role="img"
      >
        {scoreSegments(score).map((filled, index) => (
          <span
            className={`h-2.5 w-8 rounded-full ${
              filled ? "bg-slate-900" : "bg-slate-200"
            }`}
            key={`${label}-${index}`}
          />
        ))}
      </div>
    </div>
  );
}

export function ExecutivePortfolioAssessment({
  liquidity,
  positions,
}: ExecutivePortfolioAssessmentProps) {
  const liquidityScore =
    liquidity >= 70
      ? 5
      : liquidity >= 40
        ? 4
        : liquidity >= 20
          ? 3
          : 2;

  const diversificationScore =
    positions >= 15
      ? 5
      : positions >= 10
        ? 4
        : positions >= 6
          ? 3
          : 2;

  const portfolioRiskScore =
    liquidity >= 70
      ? 2
      : liquidity >= 40
        ? 3
        : liquidity >= 20
          ? 4
          : 5;

  const opportunityReadinessScore =
    liquidity >= 50
      ? 5
      : liquidity >= 25
        ? 4
        : 3;

  return (
    <section className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8">
      <div className="flex items-start gap-3">
        <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
          <ShieldCheck
            aria-hidden="true"
            className="h-5 w-5"
          />
        </div>

        <div>
          <h2 className="text-xl font-semibold tracking-tight text-slate-950">
            MOVRvest Assessment
          </h2>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Executive assessment derived from the current portfolio snapshot.
          </p>
        </div>
      </div>

      <div className="mt-6">
        <ScoreRow
          icon={Wallet}
          label="Liquidity"
          score={liquidityScore}
        />

        <ScoreRow
          icon={ChartPie}
          label="Diversification"
          score={diversificationScore}
        />

        <ScoreRow
          icon={ShieldCheck}
          label="Portfolio risk"
          score={portfolioRiskScore}
        />

        <ScoreRow
          icon={TrendingUp}
          label="Opportunity readiness"
          score={opportunityReadinessScore}
        />
      </div>
    </section>
  );
}
