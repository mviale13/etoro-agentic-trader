import { Eye } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { ObservationResponse } from "@/lib/observation-api";

type ObservationCardProps = {
  observation: ObservationResponse;
};

export function ObservationCard({
  observation,
}: ObservationCardProps) {
  return (
    <Card className="md:col-span-2">
      <div className="flex items-center gap-2">
        <Eye className="h-5 w-5 text-sky-400" />

        <div>
          <p className="text-xs uppercase tracking-wider text-slate-500">
            What I noticed
          </p>

          <h2 className="text-lg font-semibold">
            {observation.title}
          </h2>
        </div>
      </div>

      <p className="mt-6 leading-7 text-slate-300">
        {observation.message}
      </p>

      <p className="mt-6 text-xs text-slate-500">
        Observation based on your portfolio.
      </p>
    </Card>
  );
}