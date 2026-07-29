type HeaderProps = {
  greeting: string;
};

export function Header({ greeting }: HeaderProps) {
  return (
    <header className="mb-10">
      <p className="text-sm font-semibold uppercase tracking-[0.25em] text-cyan-400">
        MOVRvest
      </p>

      <h1 className="mt-3 text-4xl font-semibold">
        {greeting}
      </h1>

      <p className="mt-3 max-w-2xl text-slate-400">
        Your explainable morning investment brief.
      </p>
    </header>
  );
}