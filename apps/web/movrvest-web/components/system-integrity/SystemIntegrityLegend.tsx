"use client";

import { usePathname } from "next/navigation";

import {
  BackendStatusDot,
  type BackendStatus,
} from "@/components/system-integrity/BackendStatusDot";

type PageIntegrity = {
  status: BackendStatus;
  endpoint?: string;
  description: string;
};

// This map is maintained by hand and will drift unless it is updated
// alongside the page it describes. Where a page renders its own StatusPill
// from a real data source, that pill is the more reliable signal — keep the
// two in agreement.
const PAGE_STATUS: Record<string, PageIntegrity> = {
  "/": {
    status: "partial",
    endpoint: "/brain/ + /executive/portfolio",
    description:
      "Portfolio and executive decisions are live. The change feed has no backend source yet.",
  },
  "/brain": {
    status: "placeholder",
    description: "This route is still a workspace placeholder.",
  },
  "/portfolio": {
    status: "live",
    endpoint: "/brain/",
    description: "Real broker figures from the portfolio snapshot.",
  },
  "/investor": {
    status: "partial",
    endpoint: "/brain/",
    description:
      "Observation and investor DNA are live. Recent learning awaits the Learning layer.",
  },
  "/strategy": {
    status: "live",
    endpoint: "/strategy",
    description: "The investment policy is read from and written to the backend.",
  },
  "/briefs": {
    status: "placeholder",
    description: "This brief renders a fixed example, not your holdings.",
  },
  "/dossiers": {
    status: "placeholder",
    description: "This route is still a workspace placeholder.",
  },
  "/events": {
    status: "placeholder",
    description: "This route is still a workspace placeholder.",
  },
  "/markets": {
    status: "placeholder",
    description: "Market sections are currently static.",
  },
  "/research": {
    status: "placeholder",
    description: "Research candidates are hardcoded; no scanner feeds them.",
  },
  "/settings": {
    status: "placeholder",
    description: "Settings are currently frontend-only.",
  },
};

export function SystemIntegrityLegend() {
  const pathname = usePathname();

  const integrity =
    PAGE_STATUS[pathname] ??
    Object.entries(PAGE_STATUS).find(
      ([route]) => route !== "/" && pathname.startsWith(`${route}/`),
    )?.[1] ?? {
      status: "placeholder" as const,
      description: "Backend status has not been classified yet.",
    };

  return (
    <div className="fixed bottom-5 right-5 z-[100] rounded-xl border border-slate-200 bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
      <div className="flex items-center gap-3">
        <BackendStatusDot
          status={integrity.status}
          endpoint={integrity.endpoint}
          label="System Integrity"
          details={integrity.description}
        />

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
            System Integrity
          </p>
          <p className="text-xs font-semibold text-slate-700">
            {integrity.status === "live"
              ? "Connected"
              : integrity.status === "partial"
                ? "Partially connected"
                : "Placeholder"}
          </p>
        </div>
      </div>
    </div>
  );
}
