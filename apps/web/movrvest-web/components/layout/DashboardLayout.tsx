import type { ReactNode } from "react";

import { ExecutiveNavigation } from "@/components/layout/ExecutiveNavigation";

type DashboardLayoutProps = {
  children: ReactNode;
};

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-950">
      <ExecutiveNavigation />
      <div className="lg:pl-64">{children}</div>
    </div>
  );
}
