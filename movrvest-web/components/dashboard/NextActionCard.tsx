import { Card } from "@/components/ui/Card";

type NextActionCardProps = {
  action: string;
};

export function NextActionCard({
  action,
}: NextActionCardProps) {
  return (
    <Card className="border-cyan-500/30 bg-cyan-500/10 md:col-span-2">
      <p className="text-sm font-semibold uppercase tracking-wider text-cyan-300">
        Next Action
      </p>

      <p className="mt-3 text-xl font-medium">
        {action}
      </p>
    </Card>
  );
}