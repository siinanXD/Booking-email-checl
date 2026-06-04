import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import {
  fetchAccountMailConnection,
  fetchAccountWhatsAppInfo,
  fetchAllAccounts,
  testAccountMailConnection,
  testAccountWhatsApp,
} from "@/lib/api/admin";
import type { AdminWhatsAppTestTemplate } from "@/lib/types/api";
import { AdminPageIntro } from "@/features/admin/components/AdminPageIntro";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";

const TEMPLATE_OPTIONS: { value: AdminWhatsAppTestTemplate; label: string }[] = [
  { value: "hello_world", label: "hello_world (Meta-Standard)" },
  { value: "cleaning_task", label: "Reinigungsauftrag" },
  { value: "status_notice", label: "Status-Hinweis" },
  { value: "guest_inquiry", label: "Gastanfrage" },
];

export function AdminDiagnosticsPage() {
  const [accountId, setAccountId] = useState("");
  const [recipient, setRecipient] = useState("");
  const [template, setTemplate] = useState<AdminWhatsAppTestTemplate>("hello_world");
  const [mailResult, setMailResult] = useState<string | null>(null);
  const [waResult, setWaResult] = useState<string | null>(null);

  const { data: accounts } = useQuery({
    queryKey: ["admin-accounts", "all"],
    queryFn: fetchAllAccounts,
  });

  const activeAccounts = useMemo(
    () => accounts?.items.filter((a) => a.status === "active") ?? [],
    [accounts]
  );

  const { data: mailConnection, isLoading: mailLoading } = useQuery({
    queryKey: ["admin-mail-connection", accountId],
    queryFn: () => fetchAccountMailConnection(accountId),
    enabled: Boolean(accountId),
  });

  const { data: whatsappInfo, isLoading: waLoading } = useQuery({
    queryKey: ["admin-whatsapp-info", accountId],
    queryFn: () => fetchAccountWhatsAppInfo(accountId),
    enabled: Boolean(accountId),
  });

  const mailTestMut = useMutation({
    mutationFn: () => testAccountMailConnection(accountId),
    onSuccess: (res) => {
      setMailResult(
        res.success
          ? `OK — ${res.message}${res.mailbox_count != null ? ` (${res.mailbox_count} Nachrichten)` : ""}`
          : `Fehler: ${res.message}`
      );
    },
    onError: () => setMailResult("Postfach-Test fehlgeschlagen."),
  });

  const waTestMut = useMutation({
    mutationFn: () =>
      testAccountWhatsApp(accountId, {
        recipient_e164: recipient.trim() || undefined,
        template,
      }),
    onSuccess: (res) => {
      setWaResult(
        res.success
          ? `OK — Template ${res.template_name ?? res.template} (ID: ${res.provider_message_id ?? "—"})`
          : `Fehler: ${res.error ?? "Unbekannt"}`
      );
    },
    onError: () => setWaResult("WhatsApp-Test fehlgeschlagen."),
  });

  function handleAccountChange(id: string) {
    setAccountId(id);
    setMailResult(null);
    setWaResult(null);
    setRecipient("");
  }

  return (
    <div className="space-y-6">
      <AdminPageIntro
        title="Diagnose: Mail & WhatsApp"
        description="Wähle einen Mandanten und teste dessen gespeicherte Verbindungen — du verbindest kein eigenes Postfach. Der Mail-Test prüft IMAP/Outlook mit den Mandanten-Credentials; der WhatsApp-Test sendet eine Template-Nachricht an eine Testnummer."
        impact="Tests lösen echte Verbindungsversuche aus (max. 5 pro Minute pro Mandant). Erfolg oder Fehler werden sofort angezeigt; Credentials bleiben serverseitig und erscheinen nicht in der Antwort."
      />

      <Card className="space-y-4">
        <h2 className="text-lg font-medium text-slate-900">Mandant wählen</h2>
        <label className="block text-sm text-slate-600">
          Aktiver Mandant
          <select
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={accountId}
            onChange={(e) => handleAccountChange(e.target.value)}
          >
            <option value="">— Bitte wählen —</option>
            {activeAccounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.display_name} ({a.contact_email})
              </option>
            ))}
          </select>
        </label>
        {activeAccounts.length === 0 && (
          <p className="text-sm text-slate-500">Keine aktiven Mandanten vorhanden.</p>
        )}
      </Card>

      {accountId && (
        <>
          <Card className="space-y-4">
            <h2 className="text-lg font-medium text-slate-900">Postfach</h2>
            {mailLoading && (
              <p className="text-sm text-slate-500">Lade Postfach-Status…</p>
            )}
            {mailConnection && (
              <>
                <p className="text-sm text-slate-600">
                  {mailConnection.provider === "outlook" ? "Outlook" : "IMAP"} ·{" "}
                  {mailConnection.email_address || "—"}
                </p>
                <p className="text-sm text-slate-500">
                  Status:{" "}
                  <span
                    className={
                      mailConnection.status === "connected"
                        ? "text-green-700"
                        : mailConnection.status === "error"
                          ? "text-red-600"
                          : "text-slate-600"
                    }
                  >
                    {mailConnection.status}
                  </span>
                  {mailConnection.onboarding_completed ? "" : " · Onboarding offen"}
                </p>
                {mailConnection.last_sync_at && (
                  <p className="text-xs text-slate-500">
                    Letzter Sync:{" "}
                    {new Date(mailConnection.last_sync_at).toLocaleString("de-DE")}
                  </p>
                )}
                {mailConnection.last_error && (
                  <p className="text-xs text-red-600">{mailConnection.last_error}</p>
                )}
                <Button
                  variant="secondary"
                  disabled={mailTestMut.isPending}
                  onClick={() => mailTestMut.mutate()}
                >
                  Postfach-Verbindung testen
                </Button>
                {mailResult && (
                  <p
                    className={`text-sm ${mailResult.startsWith("OK") ? "text-green-700" : "text-red-600"}`}
                  >
                    {mailResult}
                  </p>
                )}
              </>
            )}
          </Card>

          <Card className="space-y-4">
            <h2 className="text-lg font-medium text-slate-900">WhatsApp</h2>
            {waLoading && (
              <p className="text-sm text-slate-500">Lade WhatsApp-Konfiguration…</p>
            )}
            {whatsappInfo && (
              <>
                <p className="text-sm text-slate-600">
                  Aktiv: {whatsappInfo.whatsapp_enabled ? "ja" : "nein"} · Token:{" "}
                  {whatsappInfo.access_token_configured ? "hinterlegt" : "fehlt"} ·
                  Phone ID: {whatsappInfo.phone_number_id || "—"}
                </p>
                <p className="text-xs text-slate-500">
                  Templates:{" "}
                  {Object.entries(whatsappInfo.templates)
                    .map(([k, v]) => `${k}=${v}`)
                    .join(", ")}
                </p>
                <label className="block text-sm text-slate-600">
                  Test-Template
                  <select
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={template}
                    onChange={(e) =>
                      setTemplate(e.target.value as AdminWhatsAppTestTemplate)
                    }
                  >
                    {TEMPLATE_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-sm text-slate-600">
                  Test-Empfänger (E.164)
                  <Input
                    className="mt-1"
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    placeholder={
                      whatsappInfo.test_recipient || "+491701234567"
                    }
                  />
                </label>
                <Button
                  variant="secondary"
                  disabled={waTestMut.isPending}
                  onClick={() => waTestMut.mutate()}
                >
                  WhatsApp testen
                </Button>
                {waResult && (
                  <p
                    className={`text-sm ${waResult.startsWith("OK") ? "text-green-700" : "text-red-600"}`}
                  >
                    {waResult}
                  </p>
                )}
              </>
            )}
          </Card>
        </>
      )}
    </div>
  );
}
