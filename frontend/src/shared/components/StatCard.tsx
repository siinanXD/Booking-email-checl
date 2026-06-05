import type { ReactNode } from "react";
import { Link } from "react-router-dom";

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
    <div
      className={`group rounded-xl border bg-white p-5 transition-all duration-200 ${
        highlight
          ? "border-amber-200 bg-amber-50/30 shadow-[0_0_0_1px_rgba(251,191,36,0.3),0_2px_8px_rgba(251,191,36,0.12)]"
          : "border-slate-200/80 shadow-card hover:shadow-card-hover hover:-translate-y-px"
      } ${to ? "cursor-pointer" : ""}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {title}
          </p>
          <p
            className={`mt-1.5 text-2xl font-bold tabular-nums ${
              highlight ? "text-amber-700" : "text-slate-900"
            }`}
          >
            {value}
          </p>
          {hint && (
            <p className="mt-1.5 truncate text-xs text-slate-400">{hint}</p>
          )}
        </div>
        {icon && (
          <div
            className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg ${
              highlight
                ? "bg-amber-100 text-amber-600"
                : "bg-slate-100 text-slate-500 group-hover:bg-indigo-50 group-hover:text-indigo-600"
            } transition-colors duration-200`}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
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
