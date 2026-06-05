import type { DateRangeValue } from "@/lib/dateRange";

type Props = {
  value: DateRangeValue;
  onChange: (value: DateRangeValue) => void;
};

export function DateRangeFilter({ value, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="text-sm text-slate-600">
        Von
        <input
          type="date"
          className="mt-1 block rounded-lg border border-slate-300 px-2 py-1"
          value={value.fromDate}
          onChange={(e) => onChange({ ...value, fromDate: e.target.value })}
        />
      </label>
      <label className="text-sm text-slate-600">
        Bis
        <input
          type="date"
          className="mt-1 block rounded-lg border border-slate-300 px-2 py-1"
          value={value.toDate}
          onChange={(e) => onChange({ ...value, toDate: e.target.value })}
        />
      </label>
    </div>
  );
}
