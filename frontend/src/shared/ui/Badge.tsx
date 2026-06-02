const styles: Record<string, string> = {
  pending: "bg-amber-100 text-amber-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  discarded: "bg-slate-100 text-slate-600",
  default: "bg-slate-100 text-slate-700",
};

export function Badge({
  label,
  tone = "default",
}: {
  label: string;
  tone?: string;
}) {
  const key = styles[tone] ? tone : "default";
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${styles[key]}`}
    >
      {label}
    </span>
  );
}
