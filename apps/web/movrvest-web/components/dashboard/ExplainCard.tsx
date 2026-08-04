import { Brain } from "lucide-react";

import { Card } from "@/components/ui/Card";

type ExplainCardProps = {
  recommendation: string;
  confidence: number;
  reasons: string[];
};

export function ExplainCard({
  recommendation,
  confidence,
  reasons,
}: ExplainCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Brain className="h-5 w-5 text-violet-400" />
        <h2 className="text-lg font-semibold">
          Why {recommendation}?
        </h2>
      </div>

      <p className="mt-4 text-violet-300">
        Confidence: {confidence}%
      </p>

      <ul className="mt-4 space-y-2">
        {reasons.map((reason) => (
          <li key={reason} className="text-slate-300">
            ✓ {reason}
          </li>
        ))}
      </ul>
    </Card>
  );
}