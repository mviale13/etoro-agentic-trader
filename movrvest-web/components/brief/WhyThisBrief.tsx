type WhyThisBriefProps = {
  reasons: string[];
};

export function WhyThisBrief({ reasons }: WhyThisBriefProps) {
  return (
    <section className="border-t border-slate-200 pt-7">
      <h2 className="text-xl font-semibold tracking-tight text-slate-950">
        Why This Brief?
      </h2>

      <ul className="mt-5 space-y-3">
        {reasons.map((reason) => (
          <li key={reason} className="flex items-start gap-3">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-xs font-bold text-emerald-700">
              ✓
            </span>

            <span className="text-sm leading-5 text-slate-700">{reason}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
