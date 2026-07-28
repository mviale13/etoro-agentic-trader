import { ExecutiveBrief } from "@/components/brief/ExecutiveBrief";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { microsoftExecutiveBrief } from "@/mocks/executive-brief";

export default function BriefPage() {
  return (
    <DashboardLayout>
      <ExecutiveBrief brief={microsoftExecutiveBrief} />
    </DashboardLayout>
  );
}
