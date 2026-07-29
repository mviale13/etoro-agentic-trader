import { Card } from "@/components/ui/Card";

type OpportunityCardProps = {
  symbol: string;
  action: string;
  confidence: number;
};

export function OpportunityCard({
  symbol,
  action,
  confidence,
}: OpportunityCardProps) {
  const actionStyle =
    action === "BUY"
      ? "bg-emerald-500/15 text-emerald-300"
      : action === "SELL"
        ? "bg-red-500/15 text-red-300"
        : "bg-amber-500/15 text-amber-300";

  return (
    <Card>
      <p className="text-sm text-slate-400">Today&apos;s Focus</p>

      <p className="mt-3 text-3xl font-semibold">{symbol}</p>

      <div className="mt-4 flex items-center gap-3">
        <span
          className={`rounded-full px-3 py-1 text-sm font-semibold ${actionStyle}`}
        >
          {action}
        </span>

        <span className="text-slate-400">
          {confidence}% confidence
        </span>
      </div>
    </Card>
  );
}