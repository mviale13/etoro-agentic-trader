import { ShieldCheck } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { PortfolioHealthResponse } from "@/lib/portfolio-health-api";

type PortfolioHealthCardProps = {
  health: PortfolioHealthResponse;
};

export function PortfolioHealthCard({
  health,
}: PortfolioHealthCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <ShieldCheck className="h-5 w-5 text-green-400" />
        <h2 className="text-lg font-semibold">
          Portfolio Health
        </h2>
      </div>

      <div className="mt-6">
        <p className="text-5xl font-bold text-green-400">
          {health.score}
        </p>

        <p className="mt-4 text-sm text-slate-300">
          {health.summary}
        </p>
      </div>
    </Card>
  );
}