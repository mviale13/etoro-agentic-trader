import { Activity } from "lucide-react";

import { Card } from "@/components/ui/Card";

type DoctorCardProps = {
  health: number;
  diagnosis: string[];
  prescriptions: string[];
  projectedHealth: number;
};

export function DoctorCard({
  health,
  diagnosis,
  prescriptions,
  projectedHealth,
}: DoctorCardProps) {
  const status =
    health >= 90
      ? { label: "Excellent", color: "text-emerald-400" }
      : health >= 75
        ? { label: "Good", color: "text-cyan-400" }
        : health >= 60
          ? { label: "Fair", color: "text-amber-400" }
          : { label: "Needs Attention", color: "text-red-400" };

  return (
    <Card className="transition-all duration-200 hover:-translate-y-1 hover:shadow-xl md:col-span-2">
      <div className="flex items-center gap-2">
        <Activity className="h-5 w-5 text-cyan-400" />
        <h2 className="text-lg font-semibold">Portfolio Doctor</h2>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <span className="text-slate-400">Health</span>

        <div className="text-right">
          <p className="text-2xl font-bold text-white">
            {health}/100
          </p>

          <p className={`text-sm font-medium ${status.color}`}>
            {status.label}
          </p>
        </div>
      </div>

      <div className="mt-6">
        <p className="font-medium">Diagnosis</p>

        <ul className="mt-2 space-y-2">
          {diagnosis.map((item) => (
            <li key={item} className="text-slate-300">
              ✓ {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6">
        <p className="font-medium">Prescription</p>

        <ul className="mt-2 space-y-2">
          {prescriptions.map((item) => (
            <li key={item} className="text-cyan-300">
              → {item}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-6 rounded-xl bg-cyan-500/10 p-4">
        <p className="text-sm text-cyan-300">
          Expected Health
        </p>

        <p className="mt-1 text-2xl font-bold text-white">
          {projectedHealth}/100
        </p>
      </div>
    </Card>
  );
}