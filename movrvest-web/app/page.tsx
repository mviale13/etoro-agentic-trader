import { ExecutiveWorkspace } from "@/components/executive/ExecutiveWorkspace";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { executiveWorkspaceMock } from "@/mocks/executive-workspace";

export default function Home() {
  return (
    <DashboardLayout>
      <ExecutiveWorkspace workspace={executiveWorkspaceMock} />
    </DashboardLayout>
  );
}
