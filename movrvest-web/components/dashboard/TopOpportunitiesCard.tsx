import { Trophy } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { OpportunityResponse } from "@/lib/opportunities-api";

type TopOpportunitiesCardProps = {
  opportunities: OpportunityResponse[];
};

export function TopOpportunitiesCard({
  opportunities,
}: TopOpportunitiesCardProps) {
  return (
    <Card className="md:col-span-2">
      <div className="flex items-center gap-2">
        <Trophy className="h-5 w-5 text-amber-400" />
        <h2 className="text-lg font-semibold">Top Opportunities</h2>
      </div>

      <div className="mt-6 space-y-4">
        {opportunities.map((opportunity, index) => (
          <div
            key={`${opportunity.company}-${opportunity.action}`}
            className="rounded-2xl border border-slate-800 bg-slate-950/40 p-4"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-slate-500">
                  #{index + 1}
                </p>

                <p className="mt-1 text-xl font-semibold">
                  {opportunity.company}
                </p>

                <p className="mt-2 text-sm text-slate-400">
                  {opportunity.summary}
                </p>
              </div>

              <div className="text-right">
                <p className="font-semibold text-cyan-300">
                  {opportunity.action}
                </p>

                <p className="mt-1 text-sm text-slate-400">
                  {opportunity.confidence}% confidence
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}