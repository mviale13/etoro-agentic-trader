type RiskSectionProps = {
  risks: string[];
};

export function RiskSection({
  risks,
}: RiskSectionProps) {
  return (
    <section className="border-t border-slate-200 py-12">
      <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
        Risks
      </h2>

      <p className="mt-3 max-w-2xl text-base leading-7 text-slate-600">
        The investment case remains exposed to the following uncertainties.
      </p>

      <ul className="mt-8 divide-y divide-slate-200 rounded-2xl border border-slate-200">
        {risks.map((risk, index) => (
          <li
            key={risk}
            className="flex items-start gap-4 p-5"
          >
            <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-sm font-semibold text-slate-600">
              {index + 1}
            </span>

            <p className="text-base leading-7 text-slate-700">
              {risk}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
