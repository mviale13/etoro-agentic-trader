import Link from "next/link";
import type { LucideIcon } from "lucide-react";
import { ArrowLeft, ArrowRight } from "lucide-react";

type WorkspacePlaceholderProps = {
  eyebrow: string;
  title: string;
  question: string;
  description: string;
  icon: LucideIcon;
  nextHref?: string;
  nextLabel?: string;
};

export function WorkspacePlaceholder({
  eyebrow,
  title,
  question,
  description,
  icon: Icon,
  nextHref = "/",
  nextLabel = "Return to Executive Brief",
}: WorkspacePlaceholderProps) {
  return (
    <main className="mx-auto min-h-screen w-full max-w-6xl px-5 py-10 sm:px-8 sm:py-14 lg:px-10">
      <Link
        href="/"
        className="inline-flex items-center gap-2 text-sm font-medium text-slate-500 transition hover:text-slate-950"
      >
        <ArrowLeft aria-hidden="true" className="h-4 w-4" />
        Executive Brief
      </Link>

      <section className="mt-10 max-w-3xl">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white">
          <Icon aria-hidden="true" className="h-5 w-5" />
        </div>
        <p className="mt-8 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
          {eyebrow}
        </p>
        <h1 className="mt-3 text-4xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-5xl">
          {title}
        </h1>
        <p className="mt-5 text-xl font-medium leading-8 text-slate-800">
          {question}
        </p>
        <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
          {description}
        </p>
      </section>

      <section className="mt-12 rounded-2xl border border-dashed border-slate-300 bg-white p-8">
        <p className="text-sm font-semibold text-slate-950">
          Workspace foundation ready
        </p>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
          This route now exists and is connected to the Executive Workspace.
          The next iteration will replace this foundation with live domain data
          and decision-focused components.
        </p>
        <Link
          href={nextHref}
          className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-slate-950"
        >
          {nextLabel}
          <ArrowRight aria-hidden="true" className="h-4 w-4" />
        </Link>
      </section>
    </main>
  );
}
