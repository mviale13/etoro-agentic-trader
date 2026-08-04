import { Scale } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { CommitteeWeightsResponse } from "@/lib/committee-weights-api";

type CommitteeWeightsCardProps = {
  data: CommitteeWeightsResponse;
};

export function CommitteeWeightsCard({
  data,
}: CommitteeWeightsCardProps) {
  const entries = Object.entries(data.weights);

  return (
    <Card>
      <div className="flex items-center gap-2">
        <Scale className="h-5 w-5 text-cyan-400" />

        <h2 className="text-lg font-semibold">
          Adaptive Committee
        </h2>
      </div>

      <div className="mt-6">
        <p className="text-sm uppercase tracking-wide text-slate-500">
          Market Regime
        </p>

        <p className="mt-2 text-3xl font-bold text-cyan-400">
          {data.regime}
        </p>
      </div>

      <div className="mt-6 space-y-4">
        {entries.length === 0 ? (
          <p className="text-sm text-slate-400">
            No historical weights available yet.
          </p>
        ) : (
          entries.map(([member, weight]) => {
            const percentage = Math.round(weight * 100);

            return (
              <div key={member}>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300">
                    {member}
                  </span>

                  <span className="text-sm font-semibold text-slate-100">
                    {percentage}%
                  </span>
                </div>

                <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-cyan-400"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
