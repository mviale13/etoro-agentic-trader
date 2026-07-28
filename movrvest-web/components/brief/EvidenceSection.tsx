import type { EvidenceView } from "@/types/executive-brief";

type EvidenceSectionProps = {
  evidence: EvidenceView[];
};

export function EvidenceSection({
  evidence,
}: EvidenceSectionProps) {
  return (
    <section className="border-t border-slate-200 py-12">
      <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
        Evidence
      </h2>

      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
        The assessment is supported by the following observable facts.
      </p>

      <div className="mt-8 divide-y divide-slate-200 rounded-2xl border border-slate-200">
        {evidence.map((item) => (
          <article
            key={item.label}
            className="grid gap-3 p-5 sm:grid-cols-[1fr_auto] sm:items-start"
          >
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                {item.label}
              </h3>

              <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
                {item.explanation}
              </p>
            </div>

            <p className="text-lg font-semibold tracking-tight text-slate-900 sm:text-right">
              {item.value}
            </p>
          </article>
        ))}
      </div>
    </section>
  );
}
