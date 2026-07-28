import type { CommitteeView } from "@/types/executive-brief";

type CommitteeConsensusProps = {
  committees: CommitteeView[];
};

function verdictColor(verdict: CommitteeView["verdict"]) {
  switch (verdict) {
    case "Strong support":
      return "text-emerald-700 bg-emerald-50";
    case "Support":
      return "text-blue-700 bg-blue-50";
    case "Neutral":
      return "text-amber-700 bg-amber-50";
    case "Caution":
      return "text-red-700 bg-red-50";
  }
}

export function CommitteeConsensus({
  committees,
}: CommitteeConsensusProps) {
  return (
    <section className="border-t border-slate-200 py-12">
      <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
        Committee Consensus
      </h2>

      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
        Independent investment committees reviewed this opportunity from
        different perspectives.
      </p>

      <div className="mt-8 divide-y divide-slate-200 rounded-2xl border border-slate-200">
        {committees.map((committee) => (
          <div
            key={committee.name}
            className="flex items-center justify-between p-5"
          >
            <div>
              <p className="text-lg font-medium text-slate-900">
                {committee.name}
              </p>
            </div>

            <span
              className={`rounded-full px-3 py-1 text-sm font-medium ${verdictColor(
                committee.verdict,
              )}`}
            >
              {committee.verdict}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
