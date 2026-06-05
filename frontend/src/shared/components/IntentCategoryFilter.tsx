import { INTENT_FILTER_OPTIONS } from "@/lib/intentDisplay";

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export function IntentCategoryFilter({ value, onChange }: Props) {
  return (
    <select
      className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {INTENT_FILTER_OPTIONS.map((opt) => (
        <option key={opt.value || "all"} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
