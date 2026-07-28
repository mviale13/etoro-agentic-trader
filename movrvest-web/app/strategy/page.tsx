import Link from "next/link";

export default function StrategyPage() {
  return (
    <main className="mx-auto max-w-4xl p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Investment Policy
          </h1>

          <p className="mt-2 text-slate-400">
            Define your investment objectives so the
            Brain can personalize its recommendations.
          </p>
        </div>

        <Link
          href="/"
          className="rounded-lg border px-4 py-2"
        >
          ← Dashboard
        </Link>
      </div>

      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-6">
        <h2 className="font-semibold">
          ⚠ Strategy Incomplete
        </h2>

        <p className="mt-2 text-slate-300">
          Until your Investment Policy is completed,
          MOVRvest will generate generic recommendations.
        </p>
      </div>

      <div className="mt-8 rounded-xl border p-6">
        <h2 className="text-xl font-semibold">
          Strategy
        </h2>

        <p className="mt-4 text-slate-400">
          The editable Investment Policy form will
          appear here in the next sprint.
        </p>
      </div>
    </main>
  );
}
