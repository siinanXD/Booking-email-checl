import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  AlertTriangle,
  CalendarCheck,
  Mail,
  RefreshCw,
  XCircle,
  Info,
} from "lucide-react";
import { fetchDashboardStats } from "@/lib/api/dashboard";
import { fetchMailConnection, syncMailConnection } from "@/lib/api/mail";
import { StatCard } from "@/shared/components/StatCard";
import { Button } from "@/shared/ui/Button";

function formatTimestamp(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function DashboardPage() {
  const queryClient = useQueryClient();
  const [showSyncErrors, setShowSyncErrors] = useState(false);

  const {
    data: stats,
    isLoading,
    dataUpdatedAt,
  } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 30_000,
  });

  const { data: mailConnection } = useQuery({
    queryKey: ["mail-connection"],
    queryFn: fetchMailConnection,
  });

  const syncMut = useMutation({
    mutationFn: () => syncMailConnection(),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
      void queryClient.invalidateQueries({ queryKey: ["emails"] });
      void queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      void queryClient.invalidateQueries({ queryKey: ["mail-connection"] });
    },
  });

  const loading = isLoading || !stats;
  const dash = "—";

  const syncErrors = [
    ...(syncMut.data?.item_errors ?? []),
    ...(syncMut.data?.reprocess_errors ?? []),
  ];
  const visibleSyncErrors = syncErrors.slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Übersicht</h2>
          <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
            <span>
              Aktualisiert:{" "}
              <span className="text-slate-600">
                {loading ? dash : formatTimestamp(new Date(dataUpdatedAt).toISOString())}
              </span>
            </span>
            <span className="text-slate-200">·</span>
            <span>
              Postfach-Sync:{" "}
              <span className="text-slate-600">{formatTimestamp(stats?.last_sync_at)}</span>
            </span>
            <span className="text-slate-200">·</span>
            <span>
              Letzte Mail:{" "}
              <span className="text-slate-600">
                {formatTimestamp(stats?.last_email_received_at)}
              </span>
            </span>
            <span className="text-slate-200">·</span>
            <span>
              Letzte Buchungs-Mail:{" "}
              <span className="text-slate-600">
                {formatTimestamp(stats?.last_booking_detected_at)}
              </span>
            </span>
          </div>
        </div>

        {/* Sync button */}
        <div className="flex flex-col items-end gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              setShowSyncErrors(false);
              syncMut.mutate();
            }}
            disabled={syncMut.isPending}
          >
            <RefreshCw
              size={15}
              className={syncMut.isPending ? "animate-spin" : ""}
            />
            Postfach synchronisieren
          </Button>

          {syncMut.data && (
            <div className="max-w-xs text-right">
              <p
                className={`text-xs font-medium ${
                  syncMut.data.success ? "text-emerald-700" : "text-amber-700"
                }`}
              >
                {syncMut.data.message}
              </p>
              {syncMut.data.duplicates > 0 && syncMut.data.processed === 0 && (
                <p className="text-xs text-slate-500">
                  Mails bereits bekannt — nur neue Mails werden verarbeitet.
                </p>
              )}
              {syncErrors.length > 0 && (
                <button
                  type="button"
                  className="mt-1 text-xs text-indigo-600 hover:text-indigo-500 underline"
                  onClick={() => setShowSyncErrors((open) => !open)}
                >
                  {showSyncErrors ? "Fehler ausblenden" : "Fehlerdetails"}
                </button>
              )}
              {showSyncErrors && visibleSyncErrors.length > 0 && (
                <ul className="mt-1.5 space-y-0.5 text-left text-xs text-red-600">
                  {visibleSyncErrors.map((err) => (
                    <li key={err} className="flex items-start gap-1">
                      <span className="mt-0.5">·</span>
                      <span>{err}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {syncMut.isError && (
            <p className="text-xs text-red-600">Synchronisation fehlgeschlagen.</p>
          )}
        </div>
      </div>

      {/* Notices */}
      {mailConnection?.last_error && (
        <div className="flex items-start gap-2.5 rounded-xl border border-amber-200/80 bg-amber-50 px-4 py-3">
          <AlertTriangle size={15} className="mt-0.5 flex-shrink-0 text-amber-600" />
          <p className="text-sm text-amber-800">
            <span className="font-medium">Postfach-Hinweis:</span>{" "}
            {mailConnection.last_error}
          </p>
        </div>
      )}
      {stats?.mail_fetch_unread_only && (
        <div className="flex items-start gap-2.5 rounded-xl border border-amber-200/80 bg-amber-50 px-4 py-3">
          <Info size={15} className="mt-0.5 flex-shrink-0 text-amber-600" />
          <p className="text-sm text-amber-800">
            Nur ungelesene Mails werden abgerufen (OUTLOOK_FETCH_UNREAD_ONLY) —
            gelesene Mails erscheinen nicht im Sync.
          </p>
        </div>
      )}

      {/* Primary stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Buchungs-Mails erkannt"
          value={loading ? dash : stats!.booking_emails_week}
          hint={
            loading
              ? "Statistiken werden geladen…"
              : `${stats!.booking_emails_total} gesamt · ${stats!.total_emails_week} E-Mails (7 T.) · ${stats!.total_emails_today} heute`
          }
          icon={<Mail size={20} />}
        />
        <StatCard
          title="Geprüft heute"
          value={loading ? dash : stats!.reviewed_today}
          hint="freigegeben oder abgelehnt"
        />
        <StatCard
          title="Review ausstehend"
          value={loading ? dash : stats!.pending_review}
          highlight={!loading && stats!.pending_review > 0}
          icon={<AlertTriangle size={20} />}
        />
        <StatCard
          title="Neue Buchungen"
          value={loading ? dash : stats!.new_bookings_today}
          icon={<CalendarCheck size={20} />}
        />
        <StatCard
          title="Stornos / Änderungen"
          value={
            loading
              ? dash
              : `${stats!.cancellations_today} / ${stats!.changes_today}`
          }
          icon={<XCircle size={20} />}
        />
      </div>

      {/* Secondary stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          title="Freigegeben heute"
          value={loading ? dash : stats!.processed_today}
        />
        <StatCard
          title="Spam verworfen"
          value={loading ? dash : stats!.spam_discarded_today}
        />
        <StatCard
          title="Grounding offen"
          value={
            loading
              ? dash
              : (stats!.pending_grounding_review ?? 0) > 0
                ? stats!.pending_grounding_review!
                : stats!.grounding_failures_today
          }
          hint={
            loading
              ? undefined
              : (stats!.pending_grounding_review ?? 0) > 0
                ? `${stats!.pending_grounding_review} zum Prüfen`
                : stats!.grounding_failures_today > 0
                  ? `${stats!.grounding_failures_today} heute erkannt`
                  : "Keine offenen Prüfhinweise"
          }
          icon={<AlertTriangle size={20} />}
          highlight={
            !loading &&
            ((stats!.pending_grounding_review ?? 0) > 0 ||
              stats!.grounding_failures_today > 0)
          }
          to={
            !loading &&
            ((stats!.pending_grounding_review ?? 0) > 0 ||
              stats!.grounding_failures_today > 0)
              ? "/ground-zero"
              : undefined
          }
        />
      </div>

      {/* Info banner */}
      {!loading &&
        stats!.total_emails_week > 0 &&
        stats!.booking_emails_total === 0 && (
          <div className="flex items-start gap-3 rounded-xl border border-blue-200/80 bg-blue-50 px-4 py-4">
            <Info size={16} className="mt-0.5 flex-shrink-0 text-blue-600" />
            <p className="text-sm text-blue-900">
              Es sind E-Mails eingegangen, aber keine als Buchungs-Mail erkannt. Die KI
              wertet Betreff und Inhalt aus (auch informelle Anfragen wie „ich möchte
              buchen"). Nach dem Sync müssen neue Mails die Pipeline durchlaufen — bei
              nur Duplikaten erneut mit „Postfach synchronisieren" und ggf. ?reprocess=1.
            </p>
          </div>
        )}
    </div>
  );
}
