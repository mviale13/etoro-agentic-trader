import { Settings } from "lucide-react";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { WorkspacePlaceholder } from "@/components/workspace/WorkspacePlaceholder";

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <WorkspacePlaceholder
        eyebrow="Settings"
        title="Investment policy"
        question="How should MOVRvest work for me?"
        description="Manage investor profile, objectives, time horizon, risk limits, portfolio policy, integrations, notification preferences, and decision controls."
        icon={Settings}
      />
    </DashboardLayout>
  );
}
