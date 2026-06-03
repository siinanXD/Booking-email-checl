import type { ActivityStatus } from "@/lib/types/api";

const LABELS: Record<ActivityStatus, string> = {
  active: "Aktiv",
  idle: "Inaktiv",
  never: "Noch nie",
};

const STYLES: Record<ActivityStatus, string> = {
  active: "bg-green-100 text-green-800",
  idle: "bg-amber-100 text-amber-800",
  never: "bg-slate-100 text-slate-600",
};

export function ActivityBadge({ status }: { status: ActivityStatus }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}
