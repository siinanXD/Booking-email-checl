import { FormEvent, useEffect, useRef, useState } from "react";
import { Loader2, CheckCircle2, Search } from "lucide-react";
import { Button } from "@/shared/ui/Button";
import { Input } from "@/shared/ui/Input";
import { autodiscoverImap } from "@/lib/api/mail";
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

type DiscoverState = "idle" | "loading" | "found" | "notfound";

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
  const [discoverState, setDiscoverState] = useState<DiscoverState>("idle");
  const [discoverLabel, setDiscoverLabel] = useState<string>("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const oauthConnected = Boolean(data?.outlook_oauth_connected);
  const useOAuth = provider === "outlook" && outlookAuthMode === "oauth";

  // Auto-detect IMAP provider when email changes
  useEffect(() => {
    if (provider !== "imap") return;

    const atIdx = email.indexOf("@");
    if (atIdx < 1) {
      setDiscoverState("idle");
      return;
    }
    const domain = email.slice(atIdx + 1).toLowerCase();
    if (!domain || !domain.includes(".")) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    setDiscoverState("loading");

    debounceRef.current = setTimeout(async () => {
      const result = await autodiscoverImap(domain);

      if (!result || result.source === "unknown") {
        setDiscoverState("notfound");
        return;
      }

      // Apply discovered preset
      if (result.preset_id !== "custom") {
        onPresetChange(result.preset_id);
      } else {
        onPresetChange("custom");
        if (result.host) onImapHostChange(result.host);
        if (result.port) onImapPortChange(result.port);
      }

      // Pre-fill username with email if empty
      if (!imapUsername) onImapUsernameChange(email);

      setDiscoverLabel(result.label ?? result.preset_id);
      setDiscoverState("found");
    }, 600);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email, provider]);

  return (
    <form className="mt-6 space-y-4" onSubmit={onSubmit}>
      {provider === "imap" && (
        <>
          {/* Email with auto-detect feedback */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">
              E-Mail-Adresse
            </label>
            <div className="relative">
              <Input
                type="email"
                value={email}
                onChange={(e) => {
                  onEmailChange(e.target.value);
                  setDiscoverState("idle");
                }}
                required
                placeholder="ihre@email.de"
                className="pr-9 border-white/10 bg-white/5 text-white placeholder:text-slate-600 focus:border-indigo-500/50 focus:ring-indigo-500/20"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {discoverState === "loading" && (
                  <Loader2 size={14} className="animate-spin text-indigo-400" />
                )}
                {discoverState === "found" && (
                  <CheckCircle2 size={14} className="text-emerald-400" />
                )}
                {discoverState === "notfound" && (
                  <Search size={14} className="text-slate-500" />
                )}
              </div>
            </div>

            {/* Auto-detect result */}
            {discoverState === "found" && (
              <p className="flex items-center gap-1.5 text-xs text-emerald-400">
                <CheckCircle2 size={11} />
                Anbieter erkannt: <span className="font-medium">{discoverLabel}</span>
              </p>
            )}
            {discoverState === "notfound" && (
              <p className="text-xs text-slate-500">
                Anbieter nicht erkannt — bitte manuell auswählen.
              </p>
            )}
          </div>

          {/* Provider select */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">
              Anbieter
            </label>
            <select
              className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={preset}
              onChange={(e) => {
                onPresetChange(e.target.value);
                const item = data?.imap_presets.find((p) => p.id === e.target.value);
                if (item?.host) {
                  onImapHostChange(item.host);
                  onImapPortChange(item.port);
                }
                setDiscoverState("idle");
              }}
            >
              {(data?.imap_presets ?? []).map((p) => (
                <option key={p.id} value={p.id} className="bg-slate-800">
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Custom host / port */}
          {preset === "custom" && (
            <div className="grid grid-cols-3 gap-2">
              <div className="col-span-2 space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  IMAP-Host
                </label>
                <Input
                  value={imapHost}
                  onChange={(e) => onImapHostChange(e.target.value)}
                  required
                  placeholder="imap.example.com"
                  className="border-white/10 bg-white/5 text-white placeholder:text-slate-600 focus:border-indigo-500/50 focus:ring-indigo-500/20"
                />
              </div>
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">Port</label>
                <Input
                  type="number"
                  value={imapPort}
                  onChange={(e) => onImapPortChange(Number(e.target.value) || 993)}
                  className="border-white/10 bg-white/5 text-white focus:border-indigo-500/50 focus:ring-indigo-500/20"
                />
              </div>
            </div>
          )}

          {/* Username */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">
              Benutzername
            </label>
            <Input
              value={imapUsername}
              onChange={(e) => onImapUsernameChange(e.target.value)}
              placeholder="Meist gleich wie E-Mail"
              className="border-white/10 bg-white/5 text-white placeholder:text-slate-600 focus:border-indigo-500/50 focus:ring-indigo-500/20"
            />
          </div>

          {/* Password */}
          <div className="space-y-1.5">
            <label className="block text-xs font-medium text-slate-300">
              App-Passwort
            </label>
            <Input
              type="password"
              value={imapPassword}
              onChange={(e) => onImapPasswordChange(e.target.value)}
              placeholder={
                data?.imap_password_set
                  ? "Leer lassen = gespeichertes Passwort"
                  : "App-Passwort des Anbieters"
              }
              className="border-white/10 bg-white/5 text-white placeholder:text-slate-600 focus:border-indigo-500/50 focus:ring-indigo-500/20"
            />
            <p className="text-xs text-slate-500">
              Bei GMX / Web.de unter Einstellungen → POP3/IMAP ein App-Passwort
              erstellen. Niemals dein normales Passwort verwenden.
            </p>
          </div>
        </>
      )}

      {/* Outlook */}
      {provider === "outlook" && (
        <>
          {useOAuth && (
            <div className="rounded-xl border border-white/10 bg-white/5 p-4">
              <p className="text-sm text-slate-300">
                Melden Sie sich mit Ihrem Microsoft-Konto an (Outlook.com, Hotmail,
                Microsoft 365).
              </p>
              {oauthConnected && (
                <p className="mt-2 flex items-center gap-1.5 text-sm font-medium text-emerald-400">
                  <CheckCircle2 size={14} />
                  Verbunden als {data?.email_address || data?.outlook_mailbox}
                </p>
              )}
              <Button
                type="button"
                className="mt-3 w-full py-2.5"
                disabled={oauthPending}
                onClick={onOutlookConnect}
              >
                {oauthPending
                  ? "Weiterleitung…"
                  : oauthConnected
                    ? "Erneut verbinden"
                    : "Mit Microsoft anmelden"}
              </Button>
            </div>
          )}

          <button
            type="button"
            className="text-xs text-slate-500 transition-colors hover:text-slate-300"
            onClick={() => setShowAdvancedOutlook((v) => !v)}
          >
            {showAdvancedOutlook
              ? "Erweiterte Optionen ausblenden"
              : "Erweitert: Shared Mailbox / Device Code"}
          </button>

          {showAdvancedOutlook && (
            <>
              <div className="space-y-1.5">
                <label className="block text-xs font-medium text-slate-300">
                  Auth-Modus
                </label>
                <select
                  className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-sm text-white focus:border-indigo-500/50 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  value={outlookAuthMode}
                  onChange={(e) => onOutlookAuthModeChange(e.target.value)}
                >
                  <option value="oauth" className="bg-slate-800">
                    OAuth (Browser-Anmeldung)
                  </option>
                  <option value="application" className="bg-slate-800">
                    Application (Shared Mailbox)
                  </option>
                  <option value="delegated" className="bg-slate-800">
                    Delegated (Device Code)
                  </option>
                </select>
              </div>
              {outlookAuthMode !== "oauth" && (
                <>
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-slate-300">
                      E-Mail-Adresse
                    </label>
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => onEmailChange(e.target.value)}
                      required
                      className="border-white/10 bg-white/5 text-white placeholder:text-slate-600 focus:border-indigo-500/50 focus:ring-indigo-500/20"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="block text-xs font-medium text-slate-300">
                      Mailbox (UPN)
                    </label>
                    <Input
                      value={outlookMailbox}
                      onChange={(e) => onOutlookMailboxChange(e.target.value)}
                      placeholder="vermieter@example.com"
                      className="border-white/10 bg-white/5 text-white placeholder:text-slate-600 focus:border-indigo-500/50 focus:ring-indigo-500/20"
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

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-3 py-2.5">
          <p className="text-xs text-red-300">{error}</p>
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <Button type="button" variant="ghost" className="text-slate-400 hover:text-white" onClick={onBack}>
          Zurück
        </Button>
        <Button
          type="submit"
          className="flex-1 py-2.5"
          disabled={savePending || (useOAuth && !oauthConnected)}
        >
          {savePending ? (
            <span className="flex items-center gap-2">
              <Loader2 size={14} className="animate-spin" />
              Speichern…
            </span>
          ) : (
            "Speichern & testen"
          )}
        </Button>
      </div>
    </form>
  );
}
