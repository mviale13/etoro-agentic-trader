"use client";

import { BackendStatusDot } from "@/components/system-integrity/BackendStatusDot";
import { usePageIntegrity } from "@/components/system-integrity/PageIntegrityContext";

const HEADLINE = {
  live: "Connected",
  partial: "Partially connected",
  placeholder: "Placeholder",
} as const;

/**
 * Floating summary of where the current page's data came from.
 *
 * It reports only what the page declared about itself via `<PageIntegrity>`.
 * A page that declares nothing is shown as unclassified rather than being
 * guessed at — an indicator whose whole purpose is honesty must not invent
 * its own answer.
 */
export function SystemIntegrityLegend() {
  const { integrity } = usePageIntegrity();

  return (
    <div className="fixed bottom-5 right-5 z-[100] rounded-xl border border-slate-200 bg-white/95 px-4 py-3 shadow-lg backdrop-blur">
      <div className="flex items-center gap-3">
        {integrity ? (
          <BackendStatusDot
            status={integrity.status}
            endpoint={integrity.endpoint}
            label="System Integrity"
            details={integrity.description}
          />
        ) : (
          <span
            aria-label="This page has not declared where its data comes from."
            className="h-2.5 w-2.5 rounded-full bg-slate-300 ring-4 ring-slate-300/20"
          />
        )}

        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-400">
            System Integrity
          </p>

          <p className="text-xs font-semibold text-slate-700">
            {integrity ? HEADLINE[integrity.status] : "Unclassified"}
          </p>
        </div>
      </div>
    </div>
  );
}
