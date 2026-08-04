type Props = {
  title: string;
  description: string;
};

export function ObservationCard({
  title,
  description,
}: Props) {
  return (
    <div className="rounded-2xl border border-blue-200 bg-blue-50 p-6">
      <h3 className="text-lg font-semibold text-slate-900">
        {title}
      </h3>

      <p className="mt-2 text-slate-600">
        {description}
      </p>
    </div>
  );
}
