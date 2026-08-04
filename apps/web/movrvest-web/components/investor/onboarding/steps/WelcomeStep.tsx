type Props = {
  onContinue: () => void;
};

export function StepWelcome({ onContinue }: Props) {
  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col justify-center px-8">

      <p className="text-sm font-semibold uppercase tracking-[0.3em] text-blue-600">
        Artificial CIO
      </p>

      <h1 className="mt-4 text-5xl font-bold tracking-tight text-slate-900">
        Meet your Artificial Chief Investment Officer
      </h1>

      <p className="mt-8 max-w-2xl text-xl leading-8 text-slate-600">
        Before I recommend investments, I'd like to understand both
        your portfolio and your objectives.
      </p>

      <p className="mt-4 max-w-2xl text-lg text-slate-500">
        This usually takes less than five minutes and allows every future
        recommendation to be tailored specifically to you.
      </p>

      <button
        onClick={onContinue}
        className="mt-12 w-fit rounded-xl bg-slate-900 px-8 py-4 text-lg font-medium text-white transition hover:bg-slate-800"
      >
        Let's begin →
      </button>

    </div>
  );
}
