"use client";

import { useEffect, useState } from "react";

type Props = {
  onContinue: () => void;
};

const TASKS = [
  "Connecting to your portfolio...",
  "Reading current positions...",
  "Importing transaction history...",
  "Calculating historical performance...",
  "Measuring diversification...",
  "Detecting investment patterns...",
  "Estimating your investment style...",
  "Building your investor timeline...",
  "Generating initial hypotheses...",
];

export function StepPortfolioAnalysis({ onContinue }: Props) {
  const [completed, setCompleted] = useState(0);

  useEffect(() => {
    if (completed >= TASKS.length) {
      const timer = setTimeout(onContinue, 1200);
      return () => clearTimeout(timer);
    }

    const timer = setTimeout(() => {
      setCompleted((value) => value + 1);
    }, 900);

    return () => clearTimeout(timer);
  }, [completed, onContinue]);

  const progress = Math.round((completed / TASKS.length) * 100);

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center px-8">

      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-600">
        Artificial CIO
      </p>

      <h1 className="mt-4 text-5xl font-bold text-slate-900">
        Getting to know your portfolio
      </h1>

      <p className="mt-6 max-w-2xl text-xl text-slate-600">
        Before making recommendations, I'm analysing your investment history
        to understand how you've invested so far.
      </p>

      <div className="mt-12">

        <div className="h-3 overflow-hidden rounded-full bg-slate-200">

          <div
            className="h-full rounded-full bg-slate-900 transition-all duration-700"
            style={{ width: `${progress}%` }}
          />

        </div>

        <div className="mt-3 flex justify-between text-sm text-slate-500">
          <span>Executive analysis</span>
          <span>{progress}%</span>
        </div>

      </div>

      <div className="mt-12 space-y-4">

        {TASKS.map((task, index) => {

          const done = index < completed;
          const active = index === completed;

          return (
            <div
              key={task}
              className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-4"
            >
              <div className="w-8 text-center text-xl">

                {done && "✓"}

                {!done && active && "●"}

                {!done && !active && "○"}

              </div>

              <div
                className={
                  done
                    ? "font-medium text-slate-900"
                    : active
                    ? "font-medium text-slate-700"
                    : "text-slate-400"
                }
              >
                {task}
              </div>

            </div>
          );
        })}

      </div>

    </div>
  );
}
