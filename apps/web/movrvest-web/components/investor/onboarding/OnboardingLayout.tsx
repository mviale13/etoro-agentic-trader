import type { ReactNode } from "react";

type Props = {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
};

export function OnboardingLayout({
  eyebrow,
  title,
  description,
  children,
}: Props) {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-8 py-20">

        <p className="text-sm font-semibold uppercase tracking-[0.30em] text-blue-600">
          {eyebrow}
        </p>

        <h1 className="mt-4 text-5xl font-bold tracking-tight text-slate-900">
          {title}
        </h1>

        <p className="mt-6 max-w-3xl text-xl leading-8 text-slate-600">
          {description}
        </p>

        <div className="mt-14">
          {children}
        </div>

      </div>
    </main>
  );
}
