import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Card } from "@/shared/ui/Card";

export function StatCard({
  title,
  value,
  hint,
  icon,
  highlight,
  to,
}: {
  title: string;
  value: string | number;
  hint?: string;
  icon?: ReactNode;
  highlight?: boolean;
  to?: string;
}) {
  const inner = (
    <Card
      className={`${highlight ? "ring-2 ring-amber-400 ring-offset-1" : ""} ${
        to ? "cursor-pointer transition hover:ring-2 hover:ring-amber-300" : ""
      }`}
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
  if (to) {
    return (
      <Link to={to} className="block no-underline text-inherit">
        {inner}
      </Link>
    );
  }
  return inner;
}
