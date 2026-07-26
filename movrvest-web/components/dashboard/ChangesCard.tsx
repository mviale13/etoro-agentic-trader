import { Card } from "@/components/ui/Card";

type ChangesCardProps = {
  changes: string[];
};

export function ChangesCard({
  changes,
}: ChangesCardProps) {
  return (
    <Card className="md:col-span-2">
      <p className="text-sm text-slate-400">
        What Changed
      </p>

      <ul className="mt-4 space-y-2">
        {changes.map((change) => (
          <li
            key={change}
            className="text-slate-300"
          >
            • {change}
          </li>
        ))}
      </ul>
    </Card>
  );
}