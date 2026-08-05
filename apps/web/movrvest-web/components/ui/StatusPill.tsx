type Status = "live" | "partial" | "placeholder";

type StatusPillProps = {
  status: Status;
  label?: string;
  /**
   * Why the pill says what it says, shown on hover. An amber pill with
   * no reason reads as an unexplained warning; the reason is the honesty.
   */
  explanation?: string;
};

const styles: Record<
  Status,
  {
    label: string;
    dot: string;
    container: string;
  }
> = {
  live: {
    label: "Live",
    dot: "bg-emerald-500",
    container:
      "border-emerald-200 bg-emerald-50 text-emerald-700",
  },

  partial: {
    label: "Partial",
    dot: "bg-amber-500",
    container:
      "border-amber-200 bg-amber-50 text-amber-700",
  },

  placeholder: {
    label: "Placeholder",
    dot: "bg-rose-500",
    container:
      "border-rose-200 bg-rose-50 text-rose-700",
  },
};

export function StatusPill({
  status,
  label,
  explanation,
}: StatusPillProps) {
  const config = styles[status];

  return (
    <span
      className={`inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs font-semibold ${config.container}`}
      title={explanation}
    >
      <span
        aria-hidden="true"
        className={`size-2 rounded-full ${config.dot}`}
      />

      {label ?? config.label}
    </span>
  );
}
