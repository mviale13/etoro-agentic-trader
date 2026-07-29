import { Brain } from "lucide-react";

import { Card } from "@/components/ui/Card";
import type { ReflectionResponse } from "@/lib/reflection-api";

type ReflectionCardProps = {
  reflection: ReflectionResponse;
};

export function ReflectionCard({
  reflection,
}: ReflectionCardProps) {
  return (
    <Card>
      <div className="flex items-center gap-2">
        <Brain className="h-5 w-5 text-cyan-400" />
        <h2 className="text-lg font-semibold">
          {reflection.title}
        </h2>
      </div>

      <p className="mt-4 text-sm leading-7 text-slate-300">
        {reflection.message}
      </p>

      <p className="mt-6 text-xs uppercase tracking-wider text-slate-500">
        Source: {reflection.source}
      </p>
    </Card>
  );
}