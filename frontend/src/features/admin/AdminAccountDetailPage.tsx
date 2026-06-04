import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchAdminAccountDetail } from "@/lib/api/admin";
import { AdminPageIntro } from "@/features/admin/components/AdminPageIntro";
import { ActivityBadge } from "@/features/admin/components/ActivityBadge";
import { DbCountsBarChart } from "@/features/admin/components/charts/DbCountsBarChart";
import { Card } from "@/shared/ui/Card";

function formatUsd(value: number): string {
  return `$${value.toFixed(4)}`;
}

function formatTs(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString("de-DE");
}

export function AdminAccountDetailPage() {
  const { accountId } = useParams<{ accountId: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-account-detail", accountId],
    queryFn: () => fetchAdminAccountDetail(accountId!),
    enabled: Boolean(accountId),
  });

  if (!accountId) {
    return <p className="text-sm text-red-600">Keine Mandanten-ID.</p>;
  }

  if (isLoading) {
    return <p className="text-sm text-slate-500">Lade Mandanten-Details…</p>;
  }

  if (error || !data) {
    return (
      <Card>
        <p className="text-sm text-red-600">Mandant nicht gefunden.</p>
        <Link to="/admin/overview" className="mt-2 inline-block text-sm text-indigo-600">
          ← Zur Übersicht
        </Link>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <AdminPageIntro
        title={`Mandant: ${data.account.display_name}`}
        description="Detailansicht eines einzelnen Mandanten: Nutzung, Kosten, Postfach-Status und gespeicherte Daten in MongoDB. Die Aktivitäts-Ampel entspricht der Plattform-Übersicht."
        impact="Read-only — Änderungen an Verbindungen testest du unter Diagnose; LLM-Verhalten unter LLM-Konfiguration. Freischaltung erfolgt unter Mandanten."
      />

      <div className="flex items-center justify-between gap-4">
        <div>
          <Link
            to="/admin/overview"
            className="text-sm text-indigo-600 hover:underline"
          >
            ← Plattform-Übersicht
          </Link>
          <h2 className="mt-1 text-xl font-semibold text-slate-900">
            {data.account.display_name}
          </h2>
          <p className="text-sm text-slate-500">{data.account.contact_email}</p>
        </div>
        <ActivityBadge status={data.activity_status} />
        <Link
          to={`/admin/workflows?account=${accountId}`}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Workflows verwalten
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <p className="text-sm text-slate-500">Kosten (30 Tage)</p>
          <p className="mt-1 text-2xl font-semibold">{formatUsd(data.costs_30d_usd)}</p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Tokens (30 Tage)</p>
          <p className="mt-1 text-2xl font-semibold">
            {data.tokens_30d.toLocaleString("de-DE")}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-slate-500">Verarbeitete Mails (30 Tage)</p>
          <p className="mt-1 text-2xl font-semibold">{data.mails_processed_30d}</p>
        </Card>
      </div>

      <Card className="space-y-3">
        <h3 className="font-medium text-slate-900">Postfach</h3>
        {data.mail_connection ? (
          <>
            <p className="text-sm text-slate-600">
              {data.mail_connection.provider} · {data.mail_connection.email_address || "—"}{" "}
              · Status: {data.mail_connection.status}
            </p>
            <p className="text-xs text-slate-500">
              Letzter Sync: {formatTs(data.mail_connection.last_sync_at)}
            </p>
            {data.mail_connection.last_error && (
              <p className="text-xs text-red-600">{data.mail_connection.last_error}</p>
            )}
          </>
        ) : (
          <p className="text-sm text-slate-500">Keine Postfach-Konfiguration.</p>
        )}
        <p className="text-xs text-slate-500">
          Letzte Mail: {formatTs(data.last_mail_received_at)}
        </p>
      </Card>

      <Card className="space-y-3">
        <h3 className="font-medium text-slate-900">Benutzer</h3>
        {data.users.length === 0 ? (
          <p className="text-sm text-slate-500">Keine Benutzer.</p>
        ) : (
          <ul className="space-y-1 text-sm text-slate-700">
            {data.users.map((u) => (
              <li key={u.id}>
                {u.email} <span className="text-slate-400">({u.role})</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <DbCountsBarChart counts={data.db_counts} />

      <Card className="space-y-3">
        <h3 className="font-medium text-slate-900">Datenbank-Counts (Tabelle)</h3>
        <dl className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
          {Object.entries(data.db_counts).map(([key, count]) => (
            <div key={key}>
              <dt className="text-slate-500">{key}</dt>
              <dd className="font-medium text-slate-900">{count}</dd>
            </div>
          ))}
        </dl>
      </Card>

      {data.langfuse_session_url && (
        <Card>
          <h3 className="font-medium text-slate-900">Langfuse</h3>
          <p className="mt-1 text-xs text-slate-500">
            Session: {data.latest_correlation_id}
          </p>
          <a
            href={data.langfuse_session_url}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block text-sm text-indigo-600 hover:underline"
          >
            Trace in Langfuse öffnen →
          </a>
        </Card>
      )}
    </div>
  );
}
