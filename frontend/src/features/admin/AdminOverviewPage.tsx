import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchAdminOverview } from "@/lib/api/admin";
import { StatCard } from "@/shared/components/StatCard";
import { Card } from "@/shared/ui/Card";
import { ActivityBadge } from "@/features/admin/components/ActivityBadge";

function formatUsd(value: number): string {
  return `$${value.toFixed(4)}`;
}

function formatTs(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("de-DE");
}

export function AdminOverviewPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-overview"],
    queryFn: fetchAdminOverview,
    refetchInterval: 60_000,
  });

  if (isLoading) {
    return <p className="text-sm text-slate-500">Lade Plattform-Übersicht…</p>;
  }

  if (error || !data) {
    return (
      <Card>
        <p className="text-sm text-red-600">Übersicht konnte nicht geladen werden.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Mandanten gesamt"
          value={data.total_accounts}
          hint={`${data.active_accounts} aktiv · ${data.pending_accounts} ausstehend`}
        />
        <StatCard
          title="Aktive Mandanten (7 Tage)"
          value={data.active_users_7d}
          hint="Mail-Sync, Mails, Reviews oder API-Nutzung"
        />
        <StatCard
          title="Kosten (30 Tage)"
          value={formatUsd(data.total_cost_usd_30d)}
          hint={`${data.mails_processed_30d} verarbeitete Mails`}
        />
        <StatCard
          title="Tokens (30 Tage)"
          value={data.total_tokens_30d.toLocaleString("de-DE")}
        />
      </div>

      <Card className="overflow-x-auto">
        <h2 className="mb-4 text-lg font-medium text-slate-900">Mandanten</h2>
        {data.tenants.length === 0 ? (
          <p className="text-sm text-slate-500">Keine aktiven Mandanten.</p>
        ) : (
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500">
                <th className="pb-2 pr-4 font-medium">Name</th>
                <th className="pb-2 pr-4 font-medium">Aktivität</th>
                <th className="pb-2 pr-4 font-medium">Kosten 30d</th>
                <th className="pb-2 pr-4 font-medium">Mails 30d</th>
                <th className="pb-2 pr-4 font-medium">Letzter Sync</th>
                <th className="pb-2 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {data.tenants.map((row) => (
                <tr key={row.account.id} className="border-b border-slate-100">
                  <td className="py-3 pr-4">
                    <div className="font-medium text-slate-900">
                      {row.account.display_name}
                    </div>
                    <div className="text-xs text-slate-500">
                      {row.account.contact_email}
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <ActivityBadge status={row.activity_status} />
                  </td>
                  <td className="py-3 pr-4">{formatUsd(row.costs_30d_usd)}</td>
                  <td className="py-3 pr-4">{row.mails_processed_30d}</td>
                  <td className="py-3 pr-4 text-slate-600">
                    {formatTs(row.last_sync_at)}
                  </td>
                  <td className="py-3">
                    <Link
                      to={`/admin/accounts/${row.account.id}`}
                      className="text-indigo-600 hover:underline"
                    >
                      Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
