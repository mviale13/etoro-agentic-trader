type ExecutiveAssessmentProps = {
  assessment: string[];
};

export function ExecutiveAssessment({
  assessment,
}: ExecutiveAssessmentProps) {
  return (
    <section className="rounded-2xl bg-slate-950 p-6 text-white shadow-sm sm:p-8">
      <div className="flex gap-4">
        <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-white/10 text-xl text-white">
          ☆
        </span>

        <div className="min-w-0 flex-1">
          <h2 className="text-xl font-semibold tracking-tight">
            Executive Assessment
          </h2>

          <div className="mt-5 space-y-2">
            {assessment.map((statement) => (
              <p
                key={statement}
                className="text-sm leading-6 text-slate-200"
              >
                {statement}
              </p>
            ))}
          </div>

          <p className="mt-7 border-t border-white/20 pt-6 text-sm font-medium text-white">
            Final investment decision remains yours.
          </p>
        </div>
      </div>
    </section>
  );
}
