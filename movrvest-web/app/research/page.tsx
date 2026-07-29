import { FlaskConical } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

export default function ResearchPage() {
  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow="Research"
        title="Executive ranking"
        question="What are the best companies to investigate now?"
        description="Rank investable companies by committee conviction, expected return, downside risk, evidence quality, and relevance to the portfolio."
        icon={FlaskConical}
        nextHref="/dossiers/MSFT"
        nextLabel="Open the first investment dossier"
      />
    </DashboardLayout>
  );
}
