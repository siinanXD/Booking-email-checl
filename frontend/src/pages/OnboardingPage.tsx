import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import {
  fetchMailConnection,
  saveMailConnection,
  testMailConnection,
} from "@/api/mail";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuthStore } from "@/stores/authStore";

type Provider = "imap" | "outlook";
type Step = "provider" | "config" | "test";

function isAccountAdmin(role: string | undefined): boolean {
  return role === "owner" || role === "admin" || role === "platform_admin";
}

export function OnboardingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isEditMode = searchParams.has("edit");
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const loadUser = useAuthStore((s) => s.loadUser);

  const [step, setStep] = useState<Step>("provider");
  const [provider, setProvider] = useState<Provider>("imap");
  const [preset, setPreset] = useState("gmx");
  const [email, setEmail] = useState("");
  const [imapUsername, setImapUsername] = useState("");
  const [imapPassword, setImapPassword] = useState("");
  const [imapHost, setImapHost] = useState("");
  const [imapPort, setImapPort] = useState(993);
  const [outlookMailbox, setOutlookMailbox] = useState("");
  const [outlookAuthMode, setOutlookAuthMode] = useState("application");
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["mail-connection"],
    queryFn: fetchMailConnection,
    enabled: isAccountAdmin(user?.role),
  });

  useEffect(() => {
    if (!data) return;
    setProvider((data.provider as Provider) || "imap");
    setPreset(data.preset ?? "gmx");
    setEmail(data.email_address);
    setImapUsername(data.imap_username);
    setImapHost(data.imap_host);
    setImapPort(data.imap_port);
    setOutlookMailbox(data.outlook_mailbox);
    setOutlookAuthMode(data.outlook_auth_mode);
  }, [data]);

  const saveMut = useMutation({
    mutationFn: saveMailConnection,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mail-connection"] });
      setStep("test");
      setError(null);
    },
    onError: () => setError("Speichern fehlgeschlagen."),
  });

  const testMut = useMutation({
    mutationFn: testMailConnection,
    onSuccess: (res) => {
      setTestMessage(
        res.success
          ? `Verbindung OK${res.mailbox_count != null ? ` (${res.mailbox_count} Nachrichten)` : ""}.`
          : `Fehler: ${res.message}`
      );
      void queryClient.invalidateQueries({ queryKey: ["mail-connection"] });
    },
    onError: () => setTestMessage("Test-Anfrage fehlgeschlagen."),
  });

  const finishMut = useMutation({
    mutationFn: () => saveMailConnection({ onboarding_completed: true }),
    onSuccess: async () => {
      await loadUser();
      navigate("/", { replace: true });
    },
  });

  if (!isAccountAdmin(user?.role)) {
    return <Navigate to="/" replace />;
  }

  if (user?.mail_onboarding_completed && !isEditMode) {
    return <Navigate to="/" replace />;
  }

  function handleSaveConfig(e: FormEvent) {
    e.preventDefault();
    saveMut.mutate({
      provider,
      email_address: email,
      preset: provider === "imap" ? preset : undefined,
      imap_host: imapHost,
      imap_port: imapPort,
      imap_username: imapUsername || email,
      imap_password: imapPassword || undefined,
      outlook_mailbox: outlookMailbox || email,
      outlook_auth_mode: outlookAuthMode,
    });
  }

  async function handleSkip() {
    await saveMailConnection({ onboarding_completed: true });
    await loadUser();
    navigate("/", { replace: true });
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <Card className="w-full max-w-lg">
        <h1 className="text-xl font-semibold text-slate-900">
          Postfach verbinden
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Schritt {step === "provider" ? 1 : step === "config" ? 2 : 3} von 3 —
          Buchungsmails werden aus diesem Postfach gelesen.
        </p>

        {isLoading && <p className="mt-4 text-sm text-slate-500">Lade…</p>}

        {step === "provider" && (
          <div className="mt-6 space-y-4">
            <div className="space-y-2">
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 p-3">
                <input
                  type="radio"
                  checked={provider === "imap"}
                  onChange={() => setProvider("imap")}
                />
                <span>
                  <span className="font-medium">IMAP</span>
                  <span className="block text-xs text-slate-500">
                    GMX, Web.de, Gmail, eigener Server
                  </span>
                </span>
              </label>
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 p-3">
                <input
                  type="radio"
                  checked={provider === "outlook"}
                  onChange={() => setProvider("outlook")}
                />
                <span>
                  <span className="font-medium">Microsoft Outlook</span>
                  <span className="block text-xs text-slate-500">
                    Graph API (Azure-App in .env konfiguriert)
                  </span>
                </span>
              </label>
            </div>
            <Button className="w-full" onClick={() => setStep("config")}>
              Weiter
            </Button>
          </div>
        )}

        {step === "config" && (
          <form className="mt-6 space-y-4" onSubmit={handleSaveConfig}>
            <div>
              <label className="mb-1 block text-sm text-slate-600">
                E-Mail-Adresse
              </label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {provider === "imap" && (
              <>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    Anbieter
                  </label>
                  <select
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={preset}
                    onChange={(e) => {
                      setPreset(e.target.value);
                      const item = data?.imap_presets.find(
                        (p) => p.id === e.target.value
                      );
                      if (item?.host) {
                        setImapHost(item.host);
                        setImapPort(item.port);
                      }
                    }}
                  >
                    {(data?.imap_presets ?? []).map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.label}
                      </option>
                    ))}
                  </select>
                </div>
                {preset === "custom" && (
                  <div className="grid grid-cols-3 gap-2">
                    <div className="col-span-2">
                      <label className="mb-1 block text-sm text-slate-600">
                        IMAP-Host
                      </label>
                      <Input
                        value={imapHost}
                        onChange={(e) => setImapHost(e.target.value)}
                        required
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-sm text-slate-600">
                        Port
                      </label>
                      <Input
                        type="number"
                        value={imapPort}
                        onChange={(e) =>
                          setImapPort(Number(e.target.value) || 993)
                        }
                      />
                    </div>
                  </div>
                )}
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    Benutzername
                  </label>
                  <Input
                    value={imapUsername}
                    onChange={(e) => setImapUsername(e.target.value)}
                    placeholder="Meist gleich wie E-Mail"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    App-Passwort
                  </label>
                  <Input
                    type="password"
                    value={imapPassword}
                    onChange={(e) => setImapPassword(e.target.value)}
                    placeholder={
                      data?.imap_password_set
                        ? "Leer lassen = gespeichertes Passwort"
                        : "App-Passwort des Anbieters"
                    }
                  />
                  <p className="mt-1 text-xs text-slate-500">
                    Bei GMX/Web.de unter Einstellungen → POP3/IMAP ein
                    App-Passwort erstellen.
                  </p>
                </div>
              </>
            )}

            {provider === "outlook" && (
              <>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    Auth-Modus
                  </label>
                  <select
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    value={outlookAuthMode}
                    onChange={(e) => setOutlookAuthMode(e.target.value)}
                  >
                    <option value="application">Application (Shared Mailbox)</option>
                    <option value="delegated">Delegated (Device Code)</option>
                  </select>
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">
                    Mailbox (UPN)
                  </label>
                  <Input
                    value={outlookMailbox}
                    onChange={(e) => setOutlookMailbox(e.target.value)}
                    placeholder="vermieter@example.com"
                  />
                </div>
                <p className="text-xs text-slate-500">
                  Azure Client ID und Secret werden serverseitig aus der .env
                  gelesen.
                </p>
              </>
            )}

            {error && <p className="text-sm text-red-600">{error}</p>}

            <div className="flex gap-2">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setStep("provider")}
              >
                Zurück
              </Button>
              <Button type="submit" className="flex-1" disabled={saveMut.isPending}>
                {saveMut.isPending ? "Speichern…" : "Speichern & testen"}
              </Button>
            </div>
          </form>
        )}

        {step === "test" && (
          <div className="mt-6 space-y-4">
            <p className="text-sm text-slate-600">
              Konfiguration gespeichert. Teste jetzt die Verbindung.
            </p>
            <Button
              className="w-full"
              onClick={() => testMut.mutate()}
              disabled={testMut.isPending}
            >
              {testMut.isPending ? "Teste…" : "Verbindung testen"}
            </Button>
            {testMessage && (
              <p
                className={`text-sm ${testMessage.startsWith("Fehler") ? "text-red-600" : "text-green-700"}`}
              >
                {testMessage}
              </p>
            )}
            <Button
              className="w-full"
              onClick={() => finishMut.mutate()}
              disabled={finishMut.isPending}
            >
              Fertig – zum Dashboard
            </Button>
            <Button type="button" variant="ghost" className="w-full" onClick={handleSkip}>
              Später einrichten
            </Button>
          </div>
        )}

        {step !== "test" && (
          <button
            type="button"
            className="mt-4 w-full text-center text-sm text-slate-500 hover:text-slate-700"
            onClick={handleSkip}
          >
            Überspringen
          </button>
        )}

        <p className="mt-4 text-center text-xs text-slate-400">
          Einstellungen später unter{" "}
          <Link to="/settings" className="text-indigo-600 hover:underline">
            Einstellungen
          </Link>{" "}
          ändern.
        </p>
      </Card>
    </div>
  );
}
