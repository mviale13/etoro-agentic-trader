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

const PAGE_STATUS: Record<string, PageIntegrity> = {
  "/": {
    status: "partial",
    endpoint: "/brain/",
    description: "Portfolio is live. Other executive sections may still use placeholders.",
  },
  "/brain": {
    status: "live",
    endpoint: "/brain/",
    description: "Connected to the MOVRvest Brain.",
  },
  "/portfolio": {
    status: "placeholder",
    description: "The dedicated portfolio page is not connected yet.",
  },
  "/investor": {
    status: "partial",
    endpoint: "/brain/",
    description: "Investor DNA is live. Policy and learning sections may be placeholders.",
  },
  "/strategy": {
    status: "partial",
    endpoint: "/brain/",
    description: "The current recommendation is live. Other strategy fields may be placeholders.",
  },
  "/markets": {
    status: "placeholder",
    description: "Market sections are currently static.",
  },
  "/research": {
    status: "placeholder",
    description: "Research sections are currently static.",
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
