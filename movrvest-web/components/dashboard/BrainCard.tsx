import { Brain } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { BrainResponse } from "@/lib/brain-api";

type BrainCardProps = {
  brain: BrainResponse;
};

export function BrainCard({
  brain,
}: BrainCardProps) {
  const totalValueEur =
    brain.portfolio.total_value_eur;

  return (
    <Card>
      <div className="flex items-center gap-2">
        <Brain className="h-5 w-5 text-cyan-400" />

        <h2 className="text-lg font-semibold">
          MOVRvest Brain
        </h2>
      </div>

      <p className="mt-6 text-sm text-slate-300">
        {brain.summary ?? brain.observation.message}
      </p>

      <div className="mt-4 rounded-xl bg-slate-800 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">
          Current observation
        </p>

        <p className="mt-2 font-semibold">
          {brain.observation.title}
        </p>

        <p className="mt-1 text-sm text-slate-400">
          {brain.observation.message}
        </p>
      </div>

      <div className="mt-6 grid grid-cols-3 gap-4 text-center">
        <div>
          {totalValueEur !== undefined ? (
            <>
              <p className="text-2xl font-bold">
                €{totalValueEur.toLocaleString("en-US")}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                ${brain.portfolio.total_value.toLocaleString("en-US")} USD
              </p>
            </>
          ) : (
            <p className="text-2xl font-bold">
              ${brain.portfolio.total_value.toLocaleString("en-US")}
            </p>
          )}

          <p className="mt-1 text-xs text-slate-500">
            Portfolio
          </p>
        </div>

        <div>
          <p className="text-2xl font-bold">
            {brain.portfolio.cash_allocation.toFixed(0)}%
          </p>

          <p className="text-xs text-slate-500">
            Cash
          </p>
        </div>

        <div>
          <p className="text-2xl font-bold">
            {brain.portfolio.positions}
          </p>

          <p className="text-xs text-slate-500">
            Positions
          </p>
        </div>
      </div>

      <div className="mt-6 rounded-xl bg-slate-800 p-4">
        <p className="text-xs uppercase tracking-wide text-slate-500">
          Recommendation
        </p>

        <p className="mt-2 text-lg font-semibold text-cyan-400">
          {brain.recommendation.action}{" "}
          {brain.recommendation.symbol}
        </p>

        <p className="mt-1 text-sm text-slate-400">
          {brain.recommendation.confidence}% confidence
        </p>
      </div>
    </Card>
  );
}
