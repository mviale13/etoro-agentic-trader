import { ExecutiveBrief } from "@/components/brief/ExecutiveBrief";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

type ExecutiveBriefPageProps = {
  params: Promise<{
    symbol: string;
  }>;
};

export default async function ExecutiveBriefPage({
  params,
}: ExecutiveBriefPageProps) {
  const { symbol } = await params;

  return (
    <DashboardLayout>
      <ExecutiveBrief symbol={symbol.toUpperCase()} />
    </DashboardLayout>
  );
}
