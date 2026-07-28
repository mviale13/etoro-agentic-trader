type WhyThisBriefProps = {
  reasons: string[];
};

export function WhyThisBrief({
  reasons,
}: WhyThisBriefProps) {
  return (
    <section className="border-t border-slate-200 py-12">
      <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
        Why This Brief?
      </h2>

      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
        The following developments caused MOVRvest to prepare this Executive
        Brief today.
      </p>

      <ul className="mt-8 space-y-4">
        {reasons.map((reason) => (
          <li
            key={reason}
            className="flex items-start gap-3 rounded-xl border border-slate-200 p-4"
          >
            <span className="mt-1 text-emerald-600">✓</span>

            <span className="text-base leading-7 text-slate-700">
              {reason}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
