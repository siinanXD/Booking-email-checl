import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { TrendingUp } from "lucide-react";

type Tone = "default" | "success" | "warning" | "danger" | "info" | "indigo";

const tones: Record<Tone, { border: string; iconBg: string; iconText: string; value: string }> = {
  default:  { border: "border-l-slate-300",   iconBg: "bg-slate-100",   iconText: "text-slate-500",  value: "text-slate-900"  },
  indigo:   { border: "border-l-indigo-500",  iconBg: "bg-indigo-100",  iconText: "text-indigo-600", value: "text-slate-900"  },
  success:  { border: "border-l-emerald-500", iconBg: "bg-emerald-100", iconText: "text-emerald-600",value: "text-slate-900"  },
  warning:  { border: "border-l-amber-500",   iconBg: "bg-amber-100",   iconText: "text-amber-600",  value: "text-amber-800"  },
  danger:   { border: "border-l-red-500",     iconBg: "bg-red-100",     iconText: "text-red-600",    value: "text-slate-900"  },
  info:     { border: "border-l-sky-500",     iconBg: "bg-sky-100",     iconText: "text-sky-600",    value: "text-slate-900"  },
};

export function StatCard({
  title,
  value,
  hint,
  icon,
  highlight,
  to,
  tone = "default",
}: {
  title: string;
  value: string | number;
  hint?: string;
  icon?: ReactNode;
  highlight?: boolean;
  to?: string;
  tone?: Tone;
}) {
  const resolvedTone: Tone = highlight ? "warning" : tone;
  const t = tones[resolvedTone];

  const inner = (
    <div
      className={`group relative overflow-hidden rounded-xl border-l-4 bg-white p-5 shadow-card transition-all duration-200 ${t.border} ${
        to ? "cursor-pointer hover:shadow-card-hover hover:-translate-y-0.5" : ""
      } ${highlight ? "ring-1 ring-amber-200" : "border border-slate-200/80 border-l-0"}`}
      style={{ borderLeftWidth: "4px" }}
    >
      {/* Subtle top-right decoration */}
      <div className="pointer-events-none absolute -right-4 -top-4 h-16 w-16 rounded-full opacity-[0.06] bg-current" />

      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </p>
          <p className={`mt-2 text-3xl font-extrabold tabular-nums leading-none ${t.value}`}>
            {value}
          </p>
          {hint && (
            <p className="mt-2 truncate text-xs text-slate-400">{hint}</p>
          )}
        </div>
        {icon && (
          <div
            className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl ${t.iconBg} ${t.iconText} transition-transform duration-200 group-hover:scale-110`}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Subtle trend arrow for linked cards */}
      {to && (
        <div className="mt-3 flex items-center gap-1 text-xs font-medium text-indigo-600">
          <TrendingUp size={11} />
          <span>Details ansehen</span>
        </div>
      )}
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
