import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CostSeriesPoint } from "@/types/api";

export function CostChart({ series }: { series: CostSeriesPoint[] }) {
  if (series.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-slate-500">Keine Kostendaten</p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={series}>
        <defs>
          <linearGradient id="costFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#4f46e5" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          tickFormatter={(v: string) =>
            new Date(v).toLocaleDateString("de-DE", {
              day: "2-digit",
              month: "2-digit",
            })
          }
        />
        <YAxis tick={{ fontSize: 12 }} tickFormatter={(v: number) => `$${v}`} />
        <Tooltip
          formatter={(value: number) => [`$${value.toFixed(4)}`, "Kosten"]}
          labelFormatter={(label: string) =>
            new Date(label).toLocaleDateString("de-DE")
          }
        />
        <Area
          type="monotone"
          dataKey="cost_usd"
          stroke="#4f46e5"
          fill="url(#costFill)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
