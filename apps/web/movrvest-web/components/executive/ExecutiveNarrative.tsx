"use client";

import { PenLine } from "lucide-react";
import { useEffect, useState } from "react";

import { StatusPill } from "@/components/ui/StatusPill";
import type { DossierNarrative } from "@/lib/api/dossier";

const SECTION_TITLES: Record<string, string> = {
  executive_summary: "Executive summary",
  why_now: "Why now",
  trade_off: "The trade-off",
  committee_summary: "What the committees said",
  thesis_invalidators: "What would invalidate this thesis",
};

function Narrative({ narrative }: { narrative: DossierNarrative }) {
  const findingById = new Map(
    narrative.findings.map((finding) => [finding.id, finding]),
  );

  return (
    <section
      aria-labelledby="narrative-heading"
      className="rounded-[28px] border border-slate-200 bg-white p-8"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="rounded-2xl bg-slate-100 p-3 text-slate-700">
            <PenLine aria-hidden="true" className="h-5 w-5" />
          </div>

          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Executive narrative
            </p>

            <h2
              id="narrative-heading"
              className="mt-2 text-2xl font-semibold tracking-[-0.03em] text-slate-950"
            >
              {narrative.headline}
            </h2>
          </div>
        </div>

        <StatusPill
          status="partial"
          label="AI-written, grounded"
          explanation="Written by the Executive Writer from the Artificial CIO's own findings and nothing else. Every paragraph cites its findings; the recommendation is a validated echo of the decision. The writer never decides."
        />
      </div>

      <div className="mt-6 space-y-6">
        {narrative.sections.map((section) => (
          <div key={section.section}>
            <h3 className="text-sm font-semibold uppercase tracking-[0.15em] text-slate-500">
              {SECTION_TITLES[section.section] ?? section.section}
            </h3>

            <p className="mt-2 leading-7 text-slate-700">{section.text}</p>

            <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-slate-400">
              <span>Grounded in</span>

              {section.findingIds.map((id) => (
                <span
                  className="cursor-help rounded-full bg-slate-100 px-2 py-0.5 font-medium text-slate-500"
                  key={id}
                  title={
                    findingById.get(id)
                      ? `${findingById.get(id)!.statement} — ${findingById.get(id)!.source}`
                      : id
                  }
                >
                  {id}
                </span>
              ))}
            </p>
          </div>
        ))}
      </div>

      <p className="mt-6 border-t border-slate-100 pt-4 text-xs text-slate-500">
        {narrative.written}. Language only: the structured case below is
        canonical, and the Artificial CIO owns every judgment in it.
      </p>
    </section>
  );
}

/**
 * The backend-worded reason there is no narrative.
 *
 * The Executive Writer words every failure path — flag off, missing
 * credentials, a declined request, a discarded draft — precisely so a
 * surface can state it. Presenting that sentence is this page's whole
 * job here; it adds nothing and hides nothing.
 */
function NarrativeAbsence({ reason }: { reason: string }) {
  return (
    <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-500">
      {reason}
    </p>
  );
}


/**
 * The written case, asked for after the page is already readable.
 *
 * The dossier's evidence is ready in under two seconds; wording it takes
 * fifteen to twenty, and all of that is one model call. Asking for both
 * together made the investor wait on communication for a case that was
 * already decided — so the case renders first and this fills in.
 *
 * While it is being written the wait is stated rather than hidden: an
 * empty space and a paragraph that has not arrived look the same, and
 * only one of them is worth waiting for.
 */
export function ExecutiveNarrative({ symbol }: { symbol: string }) {
  const [narrative, setNarrative] = useState<DossierNarrative | null>(null);
  const [absent, setAbsent] = useState<string | null>(null);
  const [waiting, setWaiting] = useState(true);

  useEffect(() => {
    let live = true;

    async function read() {
      try {
        const response = await fetch(
          `/api/narrative/${encodeURIComponent(symbol)}`,
          { cache: "no-store" },
        );

        const payload = await response.json();

        if (!live) {
          return;
        }

        setNarrative(parseNarrative(payload.narrative));
        setAbsent(
          typeof payload.narrative_absent === "string"
            ? payload.narrative_absent
            : null,
        );
      } catch {
        if (live) {
          setAbsent(
            "The narrative could not be requested, so the case stands as measured.",
          );
        }
      } finally {
        if (live) {
          setWaiting(false);
        }
      }
    }

    read();

    return () => {
      live = false;
    };
  }, [symbol]);

  if (waiting) {
    return (
      <p className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-5 py-4 text-sm text-slate-500">
        The Artificial CIO&apos;s case is being put into words. The decision
        and its evidence below are complete and do not depend on it.
      </p>
    );
  }

  if (narrative) {
    return <Narrative narrative={narrative} />;
  }

  return absent ? <NarrativeAbsence reason={absent} /> : null;
}

/** The wire shape, read defensively — this arrives in the browser. */
function parseNarrative(value: unknown): DossierNarrative | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const raw = value as Record<string, unknown>;

  const sections = Array.isArray(raw.sections) ? raw.sections : [];
  const findings = Array.isArray(raw.findings) ? raw.findings : [];

  if (typeof raw.headline !== "string") {
    return null;
  }

  return {
    headline: raw.headline,
    recommendation: String(raw.recommendation ?? ""),
    sections: sections.flatMap((item) => {
      const section = item as Record<string, unknown>;

      return typeof section.section === "string" &&
        typeof section.text === "string"
        ? [
            {
              section: section.section,
              text: section.text,
              findingIds: Array.isArray(section.finding_ids)
                ? section.finding_ids.map(String)
                : [],
            },
          ]
        : [];
    }),
    findings: findings.flatMap((item) => {
      const finding = item as Record<string, unknown>;

      return typeof finding.id === "string"
        ? [
            {
              id: finding.id,
              statement: String(finding.statement ?? ""),
              source: String(finding.source ?? ""),
            },
          ]
        : [];
    }),
    model: String(raw.model ?? ""),
    written: String(raw.written ?? ""),
  };
}
