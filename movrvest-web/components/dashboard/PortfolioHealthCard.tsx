import { Card } from "@/components/ui/Card";

type PortfolioHealthCardProps = {
  score: number;
  summary: string;
};

export function PortfolioHealthCard({
  score,
  summary,
}: PortfolioHealthCardProps) {
  return (
    <Card>
      <p className="text-sm text-slate-400">
        Portfolio Health
      </p>

      <p className="mt-3 text-4xl font-semibold">
        {score}
        <span className="text-xl text-slate-500">
          {" "}
          / 100
        </span>
      </p>

      <p className="mt-4 text-slate-300">
        {summary}
      </p>
    </Card>
  );
}
