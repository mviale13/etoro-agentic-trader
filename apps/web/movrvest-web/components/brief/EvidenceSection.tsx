import { StatusDot } from "@/components/ui/StatusDot";
import type { EvidenceView } from "@/types/executive-brief";

type EvidenceSectionProps = {
  evidence: EvidenceView[];
};

export function EvidenceSection({ evidence }: EvidenceSectionProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-sm font-bold text-emerald-800">
          EV
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-xl font-semibold tracking-tight text-slate-950">
              Evidence
            </h2>

            <StatusDot status="placeholder" />
          </div>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            The assessment is supported by the following observable facts.
          </p>

          <div className="mt-5 divide-y divide-slate-200">
            {evidence.map((item) => (
              <article
                key={item.label}
                className="grid gap-2 py-3 sm:grid-cols-[1fr_auto] sm:items-center"
              >
                <div>
                  <h3 className="text-sm font-medium text-slate-800">
                    {item.label}
                  </h3>

                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {item.explanation}
                  </p>
                </div>

                <p className="text-sm font-semibold text-emerald-700">
                  {item.value}
                </p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
