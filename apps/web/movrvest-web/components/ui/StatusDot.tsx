export type Status = "live" | "partial" | "placeholder";

const COLOURS: Record<Status, string> = {
  live: "bg-emerald-500",
  partial: "bg-amber-400",
  placeholder: "bg-red-500",
};

const LABELS: Record<Status, string> = {
  live: "Connected to backend",
  partial: "Partially connected",
  placeholder: "Placeholder / mock data",
};

type StatusDotProps = {
  status: Status;
};

export function StatusDot({ status }: StatusDotProps) {
  return (
    <span
      title={LABELS[status]}
      aria-label={LABELS[status]}
      className={`
        inline-block
        h-3
        w-3
        rounded-full
        ${COLOURS[status]}
        ring-2
        ring-white
        shadow-sm
      `}
    />
  );
}
