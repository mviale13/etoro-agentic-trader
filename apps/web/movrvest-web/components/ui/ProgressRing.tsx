type ProgressRingProps = {
  value: number;
  size?: number;
  strokeWidth?: number;
};

export function ProgressRing({
  value,
  size = 120,
  strokeWidth = 10,
}: ProgressRingProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const progress = Math.min(Math.max(value, 0), 100);

  const offset =
    circumference - (progress / 100) * circumference;

  const color =
    progress >= 85
      ? "#22c55e"
      : progress >= 60
        ? "#facc15"
        : "#ef4444";

  return (
    <div className="flex items-center justify-center">
      <svg width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1e293b"
          strokeWidth={strokeWidth}
          fill="none"
        />

        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />

        <text
          x="50%"
          y="50%"
          dominantBaseline="middle"
          textAnchor="middle"
          className="fill-white text-2xl font-bold"
        >
          {progress}
        </text>
      </svg>
    </div>
  );
}