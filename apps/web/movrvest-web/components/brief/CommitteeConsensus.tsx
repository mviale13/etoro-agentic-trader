import { StatusDot } from "@/components/ui/StatusDot";
import type { CommitteeView } from "@/types/executive-brief";

type CommitteeConsensusProps = {
  committees: CommitteeView[];
};

function verdictClasses(verdict: CommitteeView["verdict"]) {
  switch (verdict) {
    case "Strong support":
      return "bg-emerald-50 text-emerald-700";
    case "Support":
      return "bg-sky-50 text-sky-700";
    case "Neutral":
      return "bg-amber-50 text-amber-700";
    case "Caution":
      return "bg-rose-50 text-rose-700";
  }
}

function verdictLabel(verdict: CommitteeView["verdict"]) {
  switch (verdict) {
    case "Strong support":
      return "High conviction";
    case "Support":
      return "Positive";
    case "Neutral":
      return "Neutral";
    case "Caution":
      return "Cautious";
  }
}

export function CommitteeConsensus({
  committees,
}: CommitteeConsensusProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800">
          IC
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Committee Consensus
            </h2>

            <StatusDot status="placeholder" />
          </div>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Independent investment committees reviewed this opportunity.
          </p>

          <div className="mt-5 divide-y divide-slate-200">
            {committees.map((committee) => (
              <div
                key={committee.name}
                className="flex items-center justify-between gap-4 py-3"
              >
                <p className="text-sm font-medium text-slate-800">
                  {committee.name} Committee
                </p>

                <span
                  className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${verdictClasses(
                    committee.verdict,
                  )}`}
                >
                  {verdictLabel(committee.verdict)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
