type ExecutiveAssessmentProps = {
  assessment: string[];
};

export function ExecutiveAssessment({
  assessment,
}: ExecutiveAssessmentProps) {
  return (
    <section className="border-t border-slate-200 py-12">
      <p className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
        Final View
      </p>

      <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
        Executive Assessment
      </h2>

      <div className="mt-8 rounded-2xl bg-slate-950 p-6 text-white sm:p-8">
        <div className="space-y-4">
          {assessment.map((statement) => (
            <p
              key={statement}
              className="max-w-3xl text-base leading-7 text-slate-200"
            >
              {statement}
            </p>
          ))}
        </div>

        <div className="mt-8 border-t border-slate-800 pt-6">
          <p className="text-sm font-medium text-white">
            Final investment decision remains yours.
          </p>
        </div>
      </div>
    </section>
  );
}
