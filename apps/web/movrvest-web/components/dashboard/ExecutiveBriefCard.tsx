import { BrainResponse } from "@/lib/brain-api";
import { Card } from "@/components/ui/Card";
import { Brain } from "lucide-react";

type ExecutiveBriefCardProps = {
  brain: BrainResponse;
};

export function ExecutiveBriefCard({
  brain,
}: ExecutiveBriefCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Brain className="h-5 w-5 text-violet-400" />
        <h2 className="text-lg font-semibold">
          Executive Brief
        </h2>
      </div>

      <div className="mt-6 space-y-4">
        <div>
          <p className="text-sm text-slate-400">
            Today&apos;s Recommendation
          </p>

          <p className="mt-1 text-lg font-semibold">
            {brain.recommendation.action}
          </p>
        </div>

        <div>
          <p className="text-sm text-slate-400">
            Executive Summary
          </p>

          <p className="mt-1 leading-7">
            {brain.summary}
          </p>
        </div>

        <div>
          <p className="text-sm text-slate-400">
            Confidence
          </p>

          <p className="mt-1 font-semibold">
            {brain.recommendation.confidence}%
          </p>
        </div>
      </div>
    </Card>
  );
}
