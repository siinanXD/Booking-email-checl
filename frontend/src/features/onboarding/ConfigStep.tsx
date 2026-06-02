import { FormEvent, useState } from "react";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import type { MailConnectionResponse } from "@/lib/types/api";
import type { Provider } from "./types";

type Props = {
  provider: Provider;
  email: string;
  preset: string;
  imapUsername: string;
  imapPassword: string;
  imapHost: string;
  imapPort: number;
  outlookMailbox: string;
  outlookAuthMode: string;
  error: string | null;
  savePending: boolean;
  oauthPending: boolean;
  data: MailConnectionResponse | undefined;
  onEmailChange: (value: string) => void;
  onPresetChange: (value: string) => void;
  onImapUsernameChange: (value: string) => void;
  onImapPasswordChange: (value: string) => void;
  onImapHostChange: (value: string) => void;
  onImapPortChange: (value: number) => void;
  onOutlookMailboxChange: (value: string) => void;
  onOutlookAuthModeChange: (value: string) => void;
  onOutlookConnect: () => void;
  onBack: () => void;
  onSubmit: (e: FormEvent) => void;
};

export function ConfigStep(props: Props) {
  const {
    provider,
    email,
    preset,
    imapUsername,
    imapPassword,
    imapHost,
    imapPort,
    outlookMailbox,
    outlookAuthMode,
    error,
    savePending,
    oauthPending,
    data,
    onEmailChange,
    onPresetChange,
    onImapUsernameChange,
    onImapPasswordChange,
    onImapHostChange,
    onImapPortChange,
    onOutlookMailboxChange,
    onOutlookAuthModeChange,
    onOutlookConnect,
    onBack,
    onSubmit,
  } = props;

  const [showAdvancedOutlook, setShowAdvancedOutlook] = useState(
    outlookAuthMode !== "oauth"
  );
  const oauthConnected = Boolean(data?.outlook_oauth_connected);
  const useOAuth = provider === "outlook" && outlookAuthMode === "oauth";

  return (
    <form className="mt-6 space-y-4" onSubmit={onSubmit}>
      {provider === "imap" && (
        <div>
          <label className="mb-1 block text-sm text-slate-600">E-Mail-Adresse</label>
          <Input
            type="email"
            value={email}
            onChange={(e) => onEmailChange(e.target.value)}
            required
          />
        </div>
      )}

      {provider === "imap" && (
        <>
          <div>
            <label className="mb-1 block text-sm text-slate-600">Anbieter</label>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              value={preset}
              onChange={(e) => {
                onPresetChange(e.target.value);
                const item = data?.imap_presets.find((p) => p.id === e.target.value);
                if (item?.host) {
                  onImapHostChange(item.host);
                  onImapPortChange(item.port);
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
                <label className="mb-1 block text-sm text-slate-600">IMAP-Host</label>
                <Input
                  value={imapHost}
                  onChange={(e) => onImapHostChange(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Port</label>
                <Input
                  type="number"
                  value={imapPort}
                  onChange={(e) => onImapPortChange(Number(e.target.value) || 993)}
                />
              </div>
            </div>
          )}
          <div>
            <label className="mb-1 block text-sm text-slate-600">Benutzername</label>
            <Input
              value={imapUsername}
              onChange={(e) => onImapUsernameChange(e.target.value)}
              placeholder="Meist gleich wie E-Mail"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-600">App-Passwort</label>
            <Input
              type="password"
              value={imapPassword}
              onChange={(e) => onImapPasswordChange(e.target.value)}
              placeholder={
                data?.imap_password_set
                  ? "Leer lassen = gespeichertes Passwort"
                  : "App-Passwort des Anbieters"
              }
            />
            <p className="mt-1 text-xs text-slate-500">
              Bei GMX/Web.de unter Einstellungen → POP3/IMAP ein App-Passwort erstellen.
            </p>
          </div>
        </>
      )}

      {provider === "outlook" && (
        <>
          {useOAuth ? (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-700">
                Melden Sie sich mit Ihrem Microsoft-Konto an (Outlook.com, Hotmail, Microsoft
                365). Es wird immer die Kontoauswahl angezeigt — nicht automatisch Ihr
                zuletzt genutztes Konto.
              </p>
              {oauthConnected && (
                <p className="mt-2 text-sm font-medium text-emerald-700">
                  Verbunden als {data?.email_address || data?.outlook_mailbox}
                </p>
              )}
              <Button
                type="button"
                className="mt-3 w-full"
                disabled={oauthPending}
                onClick={onOutlookConnect}
              >
                {oauthPending
                  ? "Weiterleitung…"
                  : oauthConnected
                    ? "Erneut mit Microsoft verbinden"
                    : "Mit Microsoft anmelden"}
              </Button>
            </div>
          ) : null}

          <button
            type="button"
            className="text-sm text-slate-500 hover:text-slate-700"
            onClick={() => setShowAdvancedOutlook((v) => !v)}
          >
            {showAdvancedOutlook ? "Erweitert ausblenden" : "Erweitert: Shared Mailbox / Device Code"}
          </button>

          {showAdvancedOutlook && (
            <>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Auth-Modus</label>
                <select
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={outlookAuthMode}
                  onChange={(e) => onOutlookAuthModeChange(e.target.value)}
                >
                  <option value="oauth">OAuth (Browser-Anmeldung)</option>
                  <option value="application">Application (Shared Mailbox)</option>
                  <option value="delegated">Delegated (Device Code)</option>
                </select>
              </div>
              {outlookAuthMode !== "oauth" && (
                <>
                  <div>
                    <label className="mb-1 block text-sm text-slate-600">E-Mail-Adresse</label>
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => onEmailChange(e.target.value)}
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-sm text-slate-600">Mailbox (UPN)</label>
                    <Input
                      value={outlookMailbox}
                      onChange={(e) => onOutlookMailboxChange(e.target.value)}
                      placeholder="vermieter@example.com"
                    />
                  </div>
                </>
              )}
              <p className="text-xs text-slate-500">
                Azure Client ID und Secret werden serverseitig aus der .env gelesen.
              </p>
            </>
          )}
        </>
      )}

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex gap-2">
        <Button type="button" variant="ghost" onClick={onBack}>
          Zurück
        </Button>
        <Button
          type="submit"
          className="flex-1"
          disabled={savePending || (useOAuth && !oauthConnected)}
        >
          {savePending ? "Speichern…" : "Speichern & testen"}
        </Button>
      </div>
    </form>
  );
}
