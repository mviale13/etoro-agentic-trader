import { FileSearch } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

type DossierPageProps = {
  params: Promise<{ symbol: string }>;
};

export default async function DossierPage({ params }: DossierPageProps) {
  const { symbol } = await params;
  const normalizedSymbol = symbol.toUpperCase();

  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow={`Investment dossier · ${normalizedSymbol}`}
        title={normalizedSymbol}
        question="Should I own this company?"
        description="The full dossier will combine the executive thesis, financial health, valuation, growth, moat, catalysts, risks, committee consensus, timeline, recommendation history, and sources."
        icon={FileSearch}
        nextHref="/brain"
        nextLabel="Inspect committee reasoning"
      />
    </DashboardLayout>
  );
}
