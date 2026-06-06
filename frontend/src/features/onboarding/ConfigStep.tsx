import { FormEvent, useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { Button } from "@/shared/ui/Button";
import { autodiscoverImap } from "@/lib/api/mail";
import type { MailConnectionResponse } from "@/lib/types/api";
import type { Provider } from "./types";
import { ImapConfigFields, OutlookConfigFields } from "./ImapConfigFields";
import type { DiscoverState } from "./ImapConfigFields";

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
    provider, email, preset, imapUsername, imapPassword, imapHost, imapPort,
    outlookMailbox, outlookAuthMode, error, savePending, oauthPending, data,
    onEmailChange, onPresetChange, onImapUsernameChange, onImapPasswordChange,
    onImapHostChange, onImapPortChange, onOutlookMailboxChange,
    onOutlookAuthModeChange, onOutlookConnect, onBack, onSubmit,
  } = props;

  const [showAdvancedOutlook, setShowAdvancedOutlook] = useState(outlookAuthMode !== "oauth");
  const [discoverState, setDiscoverState] = useState<DiscoverState>("idle");
  const [discoverLabel, setDiscoverLabel] = useState<string>("");
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const oauthConnected = Boolean(data?.outlook_oauth_connected);
  const useOAuth = provider === "outlook" && outlookAuthMode === "oauth";

  useEffect(() => {
    if (provider !== "imap") return;

    const atIdx = email.indexOf("@");
    if (atIdx < 1) { setDiscoverState("idle"); return; }
    const domain = email.slice(atIdx + 1).toLowerCase();
    if (!domain || !domain.includes(".")) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    setDiscoverState("loading");

    debounceRef.current = setTimeout(async () => {
      const result = await autodiscoverImap(domain);
      if (!result || result.source === "unknown") { setDiscoverState("notfound"); return; }

      if (result.preset_id !== "custom") {
        onPresetChange(result.preset_id);
      } else {
        onPresetChange("custom");
        if (result.host) onImapHostChange(result.host);
        if (result.port) onImapPortChange(result.port);
      }
      if (!imapUsername) onImapUsernameChange(email);
      setDiscoverLabel(result.label ?? result.preset_id);
      setDiscoverState("found");
    }, 600);

    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [email, provider]);

  return (
    <form className="mt-6 space-y-4" onSubmit={onSubmit}>
      {provider === "imap" && (
        <ImapConfigFields
          email={email}
          preset={preset}
          imapUsername={imapUsername}
          imapPassword={imapPassword}
          imapHost={imapHost}
          imapPort={imapPort}
          discoverState={discoverState}
          discoverLabel={discoverLabel}
          data={data}
          onEmailChange={onEmailChange}
          onPresetChange={onPresetChange}
          onImapUsernameChange={onImapUsernameChange}
          onImapPasswordChange={onImapPasswordChange}
          onImapHostChange={onImapHostChange}
          onImapPortChange={onImapPortChange}
          onDiscoverReset={() => setDiscoverState("idle")}
        />
      )}

      {provider === "outlook" && (
        <OutlookConfigFields
          email={email}
          outlookMailbox={outlookMailbox}
          outlookAuthMode={outlookAuthMode}
          oauthPending={oauthPending}
          oauthConnected={oauthConnected}
          data={data}
          showAdvanced={showAdvancedOutlook}
          onToggleAdvanced={() => setShowAdvancedOutlook((v) => !v)}
          onEmailChange={onEmailChange}
          onOutlookMailboxChange={onOutlookMailboxChange}
          onOutlookAuthModeChange={onOutlookAuthModeChange}
          onOutlookConnect={onOutlookConnect}
        />
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
