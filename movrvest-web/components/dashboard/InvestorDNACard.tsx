import { Dna } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { InvestorDNAResponse } from "@/lib/investor-dna-api";

type InvestorDNACardProps = {
  dna: InvestorDNAResponse;
};

export function InvestorDNACard({
  dna,
}: InvestorDNACardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Dna className="h-5 w-5 text-purple-400" />

        <h2 className="text-lg font-semibold">
          Investor DNA
        </h2>
      </div>

      <div className="mt-6">
        <p className="text-5xl font-bold text-purple-400">
          {dna.understanding}%
        </p>

        <p className="mt-2 text-sm uppercase tracking-wide text-slate-500">
          Understanding
        </p>

        <p className="mt-4 text-sm text-slate-300">
          {dna.message}
        </p>
      </div>
    </Card>
  );
}