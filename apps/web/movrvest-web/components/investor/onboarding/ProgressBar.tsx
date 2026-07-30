type Props = {
  value: number;
};

export function ProgressBar({ value }: Props) {
  return (
    <div>

      <div className="h-3 overflow-hidden rounded-full bg-slate-200">
        <div
          className="h-full rounded-full bg-slate-900 transition-all duration-700"
          style={{ width: `${value}%` }}
        />
      </div>

      <div className="mt-2 flex justify-between text-sm text-slate-500">
        <span>Artificial CIO Analysis</span>
        <span>{value}%</span>
      </div>

    </div>
  );
}
