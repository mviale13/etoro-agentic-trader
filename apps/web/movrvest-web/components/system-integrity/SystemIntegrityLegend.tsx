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

  // Application chrome, not investment content: the legend sits in the
  // navigation rail's footer rather than floating over the page. The
  // sidebar collapses to a top bar on small screens and the legend is
  // hidden with the rest of its footer there — unobtrusive, and never
  // between the investor and the evidence.
  return (
    <div className="mt-6 hidden rounded-xl border border-slate-800 bg-slate-900/60 px-3 py-2.5 lg:block">
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
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            System Integrity
          </p>

          <p className="text-xs font-semibold text-slate-300">
            {integrity ? HEADLINE[integrity.status] : "Unclassified"}
          </p>
        </div>
      </div>
    </div>
  );
}
