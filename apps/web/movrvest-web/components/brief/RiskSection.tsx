import { StatusDot } from "@/components/ui/StatusDot";

type RiskSectionProps = {
  risks: string[];
};

export function RiskSection({ risks }: RiskSectionProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800">
          RK
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Risks
            </h2>

            <StatusDot status="placeholder" />
          </div>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            The investment case remains exposed to the following uncertainties.
          </p>

          <ol className="mt-5 space-y-3">
            {risks.map((risk, index) => (
              <li key={risk} className="flex items-start gap-3">
                <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-slate-950 text-[10px] font-semibold text-white">
                  {index + 1}
                </span>

                <p className="text-sm leading-5 text-slate-700">{risk}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
