type Props = {
  title: string;
  confidence: number;
  evidence: string[];
};

export function HypothesisCard({
  title,
  confidence,
  evidence,
}: Props) {
  return (
    <div className="rounded-2xl border border-violet-200 bg-violet-50 p-6">

      <div className="flex items-center justify-between">

        <h3 className="text-lg font-semibold text-slate-900">
          {title}
        </h3>

        <span className="rounded-full bg-violet-600 px-3 py-1 text-sm font-semibold text-white">
          {confidence}%
        </span>

      </div>

      <p className="mt-4 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Evidence
      </p>

      <ul className="mt-3 space-y-2">

        {evidence.map((item) => (
          <li
            key={item}
            className="text-slate-700"
          >
            • {item}
          </li>
        ))}

      </ul>

      <div className="mt-6 flex gap-3">

        <button className="rounded-lg bg-slate-900 px-4 py-2 text-white">
          Yes
        </button>

        <button className="rounded-lg border border-slate-300 px-4 py-2">
          Partially
        </button>

        <button className="rounded-lg border border-slate-300 px-4 py-2">
          No
        </button>

      </div>

    </div>
  );
}
