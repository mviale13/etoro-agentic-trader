export type BackendStatus = "live" | "partial" | "placeholder";

type BackendStatusDotProps = {
  status: BackendStatus;
  endpoint?: string;
  label?: string;
  details?: string;
  className?: string;
};

const STATUS_CONFIG = {
  live: {
    colour: "bg-emerald-500",
    ring: "ring-emerald-500/20",
    text: "Connected",
  },
  partial: {
    colour: "bg-amber-400",
    ring: "ring-amber-400/20",
    text: "Partially connected",
  },
  placeholder: {
    colour: "bg-red-500",
    ring: "ring-red-500/20",
    text: "Placeholder",
  },
} as const;

export function BackendStatusDot({
  status,
  endpoint,
  label,
  details,
  className = "",
}: BackendStatusDotProps) {
  const config = STATUS_CONFIG[status];

  const tooltip = [
    label ?? config.text,
    endpoint ? `Source: ${endpoint}` : undefined,
    details,
  ]
    .filter(Boolean)
    .join("\n");

  return (
    <span
      className={`group relative inline-flex shrink-0 ${className}`}
      aria-label={tooltip}
    >
      <span
        className={`h-2.5 w-2.5 rounded-full ${config.colour} ring-4 ${config.ring}`}
      />

      <span
        role="tooltip"
        className="pointer-events-none absolute right-0 top-5 z-50 hidden min-w-48 whitespace-pre-line rounded-lg border border-slate-200 bg-white px-3 py-2 text-left text-xs font-medium leading-5 text-slate-700 shadow-xl group-hover:block"
      >
        {tooltip}
      </span>
    </span>
  );
}
