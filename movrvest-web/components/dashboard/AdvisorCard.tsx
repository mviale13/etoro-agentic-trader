import { Target } from "lucide-react";

import { Card } from "@/components/ui/Card";

type AdvisorCardProps = {
  symbol: string;
  action: string;
  confidence: number;
};

export function AdvisorCard({
  symbol,
  action,
  confidence,
}: AdvisorCardProps) {
  return (
    <Card className="border-cyan-500/30 bg-cyan-500/5">
      <div className="flex items-center gap-2">
        <Target className="h-5 w-5 text-cyan-400" />

        <h2 className="text-lg font-semibold">
          Today&apos;s Best Opportunity
        </h2>
      </div>

      <p className="mt-6 text-4xl font-bold">
        {symbol}
      </p>

      <p className="mt-2 text-cyan-300">
        {action}
      </p>

      <p className="mt-6 text-sm text-slate-400">
        Confidence
      </p>

      <p className="text-2xl font-semibold">
        {confidence}%
      </p>
    </Card>
  );
}