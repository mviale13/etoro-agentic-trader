import { Wallet } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { PortfolioResponse } from "@/lib/portfolio-api";

type PortfolioCardProps = {
  portfolio: PortfolioResponse;
};

export function PortfolioCard({
  portfolio,
}: PortfolioCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Wallet className="h-5 w-5 text-emerald-400" />
        <h2 className="text-lg font-semibold">Your Portfolio</h2>
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <p className="text-sm text-slate-400">Total Value</p>

          <p className="text-3xl font-bold">
            ${portfolio.total_value.toLocaleString("en-US")}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-400">Cash</p>

            <p className="font-semibold">
              {portfolio.allocation.cash.toFixed(1)}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">Positions</p>

            <p className="font-semibold">{portfolio.positions}</p>
          </div>
        </div>
      </div>
    </Card>
  );
}