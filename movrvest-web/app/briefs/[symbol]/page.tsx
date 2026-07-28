import { ExecutiveBrief } from "@/components/brief/ExecutiveBrief";
import { DashboardLayout } from "@/components/layout/DashboardLayout";

interface PageProps {
  params: Promise<{
    symbol: string;
  }>;
}

export default async function BriefPage({ params }: PageProps) {
  const { symbol } = await params;

  return (
    <DashboardLayout>
      <ExecutiveBrief symbol={symbol.toUpperCase()} />
    </DashboardLayout>
  );
}
