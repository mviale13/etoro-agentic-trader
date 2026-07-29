import { BriefcaseBusiness } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

export default function PortfolioPage() {
  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow="Portfolio"
        title="Portfolio health"
        question="How healthy is my portfolio?"
        description="Review concentration, diversification, risk, cash allocation, strengths, weaknesses, and the actions that deserve attention."
        icon={BriefcaseBusiness}
        nextHref="/research"
        nextLabel="Explore ranked research"
      />
    </DashboardLayout>
  );
}
