import { ChartNoAxesCombined } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

export default function MarketsPage() {
  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow="Markets"
        title="Market intelligence"
        question="What changed in the world?"
        description="Understand the market regime, breadth, sector rotation, macro conditions, volatility, and the events that may alter investment cases."
        icon={ChartNoAxesCombined}
        nextHref="/brain"
        nextLabel="Review committee reasoning"
      />
    </DashboardLayout>
  );
}
