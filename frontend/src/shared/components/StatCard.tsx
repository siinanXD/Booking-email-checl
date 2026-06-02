import type { ReactNode } from "react";
import { Card } from "@/shared/ui/Card";

export function StatCard({
  title,
  value,
  hint,
  icon,
  highlight,
}: {
  title: string;
  value: string | number;
  hint?: string;
  icon?: ReactNode;
  highlight?: boolean;
}) {
  return (
    <Card
      className={highlight ? "ring-2 ring-amber-400 ring-offset-1" : ""}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm text-slate-500">{title}</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
          {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
        </div>
        {icon && <div className="text-slate-400">{icon}</div>}
      </div>
    </Card>
  );
}
