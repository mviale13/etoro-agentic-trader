import { Wallet } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { StatusDot } from "@/components/ui/StatusDot";
import type { PortfolioResponse } from "@/lib/portfolio-api";

type PortfolioCardProps = {
  portfolio: PortfolioResponse;
};

function formatCurrency(value: number, currency: "EUR" | "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatLastSync(value: string | null): string {
  if (!value) {
    return "Sync time unavailable";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Sync time unavailable";
  }

  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function PortfolioCard({
  portfolio,
}: PortfolioCardProps) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Wallet className="h-5 w-5 text-emerald-400" />

          <h2 className="text-lg font-semibold">
            Your Portfolio
          </h2>
        </div>

        <StatusDot status="live" />
      </div>

      <div className="mt-6 space-y-5">
        <div>
          <p className="text-sm text-slate-400">
            Total Value
          </p>

          <p className="text-3xl font-bold">
            {formatCurrency(portfolio.total_value_eur, "EUR")}
          </p>

          <p className="mt-2 text-lg text-slate-400">
            Broker value: {formatCurrency(portfolio.total_value, "USD")}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-slate-400">
              Available Cash
            </p>

            <p className="font-semibold">
              {formatCurrency(portfolio.available_cash_eur, "EUR")}
            </p>

            <p className="text-xs text-slate-500">
              {formatCurrency(portfolio.available_cash_usd, "USD")}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Invested
            </p>

            <p className="font-semibold">
              {formatCurrency(portfolio.invested_eur, "EUR")}
            </p>

            <p className="text-xs text-slate-500">
              {formatCurrency(portfolio.invested_usd, "USD")}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Liquidity
            </p>

            <p className="font-semibold">
              {portfolio.liquidity_pct.toFixed(1)}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-400">
              Positions
            </p>

            <p className="font-semibold">
              {portfolio.positions}
            </p>
          </div>
        </div>

        <div className="border-t border-slate-800 pt-4 text-xs text-slate-500">
          <p>Source: {portfolio.source}</p>
          <p>Last sync: {formatLastSync(portfolio.last_sync)}</p>
        </div>
      </div>
    </Card>
  );
}
