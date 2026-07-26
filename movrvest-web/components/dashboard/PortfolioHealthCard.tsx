import { Card } from "@/components/ui/Card";
import { ProgressRing } from "@/components/ui/ProgressRing";

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

      <div className="mt-6 flex justify-center">
        <ProgressRing value={score} />
      </div>

      <p className="mt-6 text-center text-slate-300">
        {summary}
      </p>
    </Card>
  );
}
