import { Brain } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

export default function BrainPage() {
  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow="Brain"
        title="Executive Committee"
        question="Why does MOVRvest believe this?"
        description="Inspect committee opinions, disagreements, confidence, evidence, decision history, and the reasoning behind each recommendation."
        icon={Brain}
        nextHref="/portfolio"
        nextLabel="Review portfolio implications"
      />
    </DashboardLayout>
  );
}
