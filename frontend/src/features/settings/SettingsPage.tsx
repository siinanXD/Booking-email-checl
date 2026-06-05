import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Mail, CheckCircle2, XCircle, AlertCircle, Save, Shield } from "lucide-react";
import { useAuthStore } from "@/features/auth/authStore";
import { fetchMailConnection, testMailConnection } from "@/lib/api/mail";
import { fetchSettings, saveSettings, testWhatsApp, wipeAllData } from "@/lib/api/settings";
import { SettingsDangerZone } from "@/features/settings/SettingsDangerZone";
import { SettingsWhatsAppCard } from "@/features/settings/SettingsWhatsAppCard";
import { SettingsWhatsAppRecipientsCard } from "@/features/settings/SettingsWhatsAppRecipientsCard";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";

function SectionHeader({ title, action }: { title: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
      {action}
    </div>
  );
}

const mailStatusConfig = {
  connected: { color: "text-emerald-700", bg: "bg-emerald-50", ring: "ring-emerald-200/80", icon: CheckCircle2, label: "Verbunden" },
  error: { color: "text-red-700", bg: "bg-red-50", ring: "ring-red-200/80", icon: XCircle, label: "Fehler" },
  default: { color: "text-slate-600", bg: "bg-slate-100", ring: "ring-slate-200/80", icon: AlertCircle, label: "Unbekannt" },
};

export function SettingsPage() {
  const isPlatformAdmin = useAuthStore((s) => s.isPlatformAdmin());
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
    enabled: !isPlatformAdmin,
  });

  const [whatsappEnabled, setWhatsappEnabled] = useState(false);
  const [accessToken, setAccessToken] = useState("");
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [defaultRecipients, setDefaultRecipients] = useState("");
  const [testRecipient, setTestRecipient] = useState("");
  const [userPhone, setUserPhone] = useState("");
  const [userWhatsappEnabled, setUserWhatsappEnabled] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [wipeConfirm, setWipeConfirm] = useState("");

  const { data: mailData } = useQuery({
    queryKey: ["mail-connection"],
    queryFn: fetchMailConnection,
    enabled: !isPlatformAdmin,
  });

  const mailTestMut = useMutation({
    mutationFn: testMailConnection,
    onSuccess: (res) => {
      setSaveMessage(
        res.success
          ? `Postfach-Verbindung OK${res.mailbox_count != null ? ` (${res.mailbox_count} Nachrichten)` : ""}.`
          : `Postfach-Test fehlgeschlagen: ${res.message}`
      );
    },
    onError: () => setSaveMessage("Postfach-Test fehlgeschlagen."),
  });

  useEffect(() => {
    if (!data) return;
    setWhatsappEnabled(data.whatsapp_enabled);
    setAccessToken("");
    setPhoneNumberId(data.whatsapp_phone_number_id);
    setDefaultRecipients(data.whatsapp_default_recipients);
    setTestRecipient(data.whatsapp_test_recipient);
    setUserPhone(data.user_profile.whatsapp_phone_e164 ?? "");
    setUserWhatsappEnabled(data.user_profile.whatsapp_enabled);
  }, [data]);

  const saveMut = useMutation({
    mutationFn: () =>
      saveSettings({
        whatsapp_enabled: whatsappEnabled,
        whatsapp_access_token: accessToken.trim() || undefined,
        whatsapp_phone_number_id: phoneNumberId,
        whatsapp_default_recipients: defaultRecipients,
        whatsapp_test_recipient: testRecipient,
        user_profile: {
          whatsapp_phone_e164: userPhone.trim() || null,
          whatsapp_enabled: userWhatsappEnabled,
        },
      }),
    onSuccess: () => {
      setSaveMessage("Einstellungen gespeichert.");
      setAccessToken("");
      void queryClient.invalidateQueries({ queryKey: ["settings"] });
    },
    onError: () => setSaveMessage("Speichern fehlgeschlagen."),
  });

  const testMut = useMutation({
    mutationFn: () => testWhatsApp(testRecipient || undefined),
    onSuccess: (res) => {
      setTestMessage(
        res.success
          ? `Test erfolgreich (ID: ${res.provider_message_id ?? "—"})`
          : `Test fehlgeschlagen: ${res.error ?? "Unbekannter Fehler"}`
      );
    },
    onError: () => setTestMessage("Test-Anfrage fehlgeschlagen."),
  });

  const wipeMut = useMutation({
    mutationFn: wipeAllData,
    onSuccess: (res) => {
      const total = Object.values(res.deleted).reduce((a, b) => a + b, 0);
      setSaveMessage(`Alle Daten gelöscht (${total} Dokumente).`);
      setWipeConfirm("");
      void queryClient.invalidateQueries();
    },
    onError: () => setSaveMessage("Löschen fehlgeschlagen."),
  });

  if (isPlatformAdmin) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Einstellungen</h2>
          <p className="mt-0.5 text-sm text-slate-500">
            Als Plattform-Administrator verwaltest du Mandanten über die{" "}
            <Link to="/admin/overview" className="text-indigo-600 hover:underline">
              Admin-Konsole
            </Link>
            .
          </p>
        </div>
        <Card>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-100 text-indigo-600">
              <Shield size={18} />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-800">Plattform-Administration</p>
              <p className="text-xs text-slate-500">
                Verbindungstests pro Mandant unter Admin → Diagnose.
              </p>
            </div>
          </div>
        </Card>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-10 text-slate-500">
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-500" />
        <span className="text-sm">Einstellungen werden geladen…</span>
      </div>
    );
  }

  const mailStatus = mailData?.status === "connected"
    ? mailStatusConfig.connected
    : mailData?.status === "error"
      ? mailStatusConfig.error
      : mailStatusConfig.default;

  const MailStatusIcon = mailStatus.icon;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-900">Einstellungen</h2>
        <p className="mt-0.5 text-sm text-slate-500">
          Werte aus der <code className="rounded bg-slate-100 px-1 py-0.5 text-xs">.env</code> werden
          automatisch vorausgefüllt. Nach dem Speichern gelten die Einträge dauerhaft in der Datenbank.
        </p>
      </div>

      {/* Profile */}
      <Card>
        <div className="space-y-4">
          <SectionHeader title="Mein Profil (Host)" />
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-600">
              Meine WhatsApp-Nummer (E.164, z. B. +491701234567)
            </label>
            <Input
              value={userPhone}
              onChange={(e) => setUserPhone(e.target.value)}
              placeholder="+491701234567"
            />
          </div>
          <label className="flex cursor-pointer items-center gap-2.5">
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 accent-indigo-600"
              checked={userWhatsappEnabled}
              onChange={(e) => setUserWhatsappEnabled(e.target.checked)}
            />
            <span className="text-sm text-slate-700">
              WhatsApp-Benachrichtigungen für mich aktiv
            </span>
          </label>
        </div>
      </Card>

      <SettingsWhatsAppRecipientsCard />

      <SettingsWhatsAppCard
        data={data}
        whatsappEnabled={whatsappEnabled}
        onWhatsappEnabledChange={setWhatsappEnabled}
        accessToken={accessToken}
        onAccessTokenChange={setAccessToken}
        phoneNumberId={phoneNumberId}
        onPhoneNumberIdChange={setPhoneNumberId}
        defaultRecipients={defaultRecipients}
        onDefaultRecipientsChange={setDefaultRecipients}
        testRecipient={testRecipient}
        onTestRecipientChange={setTestRecipient}
        testPending={testMut.isPending}
        onTest={() => testMut.mutate()}
        testMessage={testMessage}
      />

      {/* Mail connection */}
      <Card>
        <div className="space-y-4">
          <SectionHeader
            title="Postfach"
            action={
              <Link to="/onboarding?edit=1" className="text-xs font-medium text-indigo-600 hover:text-indigo-500">
                Bearbeiten
              </Link>
            }
          />
          {mailData ? (
            <>
              <div className="flex items-center gap-3 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3">
                <Mail size={16} className="flex-shrink-0 text-slate-400" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-800">
                    {mailData.provider === "outlook" ? "Microsoft Outlook" : "IMAP"}
                    {mailData.email_address && (
                      <span className="font-normal text-slate-500"> · {mailData.email_address}</span>
                    )}
                  </p>
                  {mailData.last_sync_at && (
                    <p className="text-xs text-slate-400">
                      Letzter Sync: {new Date(mailData.last_sync_at).toLocaleString("de-DE")}
                    </p>
                  )}
                </div>
                <span
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${mailStatus.bg} ${mailStatus.color} ${mailStatus.ring}`}
                >
                  <MailStatusIcon size={12} />
                  {mailStatus.label}
                </span>
              </div>
              {mailData.last_error && (
                <p className="flex items-start gap-1.5 text-xs text-red-600">
                  <XCircle size={13} className="mt-0.5 flex-shrink-0" />
                  {mailData.last_error}
                </p>
              )}
              <Button
                variant="secondary"
                size="sm"
                onClick={() => mailTestMut.mutate()}
                disabled={mailTestMut.isPending}
              >
                {mailTestMut.isPending ? "Teste…" : "Verbindung testen"}
              </Button>
            </>
          ) : (
            <p className="text-sm text-slate-500">
              Noch kein Postfach verbunden.{" "}
              <Link to="/onboarding?edit=1" className="text-indigo-600 hover:underline">
                Jetzt einrichten
              </Link>
            </p>
          )}
        </div>
      </Card>

      {/* Save */}
      <div className="flex flex-wrap items-center gap-3">
        <Button onClick={() => saveMut.mutate()} disabled={saveMut.isPending}>
          <Save size={15} />
          {saveMut.isPending ? "Speichern…" : "Einstellungen speichern"}
        </Button>
        {saveMessage && (
          <p
            className={`text-sm ${
              saveMessage.includes("fehlgeschlagen") ? "text-red-600" : "text-emerald-700"
            }`}
          >
            {saveMessage}
          </p>
        )}
      </div>

      <SettingsDangerZone
        wipeConfirm={wipeConfirm}
        onWipeConfirmChange={setWipeConfirm}
        onWipe={() => wipeMut.mutate()}
        wipePending={wipeMut.isPending}
      />
    </div>
  );
}
