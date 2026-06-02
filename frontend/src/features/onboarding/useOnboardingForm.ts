import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  fetchMailConnection,
  fetchOutlookAuthorizeUrl,
  saveMailConnection,
  testMailConnection,
} from "@/lib/api/mail";
import { useAuthStore } from "@/features/auth/authStore";
import type { Provider, Step } from "./types";

export function useOnboardingForm(enabled: boolean) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const queryClient = useQueryClient();
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
  const [outlookAuthMode, setOutlookAuthMode] = useState("oauth");
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [oauthPending, setOauthPending] = useState(false);

  const oauthHandled = useRef(false);

  const { data, isLoading } = useQuery({
    queryKey: ["mail-connection"],
    queryFn: fetchMailConnection,
    enabled,
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
    setOutlookAuthMode(data.outlook_auth_mode || "oauth");
  }, [data]);

  useEffect(() => {
    if (oauthHandled.current) return;
    const outlook = searchParams.get("outlook");
    if (!outlook) return;
    oauthHandled.current = true;

    if (outlook === "connected") {
      void queryClient.invalidateQueries({ queryKey: ["mail-connection"] });
      setStep("test");
      setError(null);
      setOauthPending(false);
    } else if (outlook === "error") {
      setError(
        searchParams.get("outlook_message") || "Microsoft-Anmeldung fehlgeschlagen."
      );
      setStep("config");
      setOauthPending(false);
    }

    const next = new URLSearchParams(searchParams);
    next.delete("outlook");
    next.delete("outlook_message");
    setSearchParams(next, { replace: true });
  }, [queryClient, searchParams, setSearchParams]);

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

  function handleSaveConfig(e: FormEvent) {
    e.preventDefault();
    if (provider === "outlook" && outlookAuthMode === "oauth" && !data?.outlook_oauth_connected) {
      setError("Bitte zuerst mit Microsoft anmelden.");
      return;
    }
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

  async function handleOutlookConnect() {
    setOauthPending(true);
    setError(null);
    try {
      await saveMailConnection({
        provider: "outlook",
        outlook_auth_mode: "oauth",
      });
      const returnTo = searchParams.has("edit") ? "/onboarding?edit=1" : "/onboarding";
      const url = await fetchOutlookAuthorizeUrl(returnTo, window.location.origin);
      window.location.assign(url);
    } catch {
      setError("Microsoft-Anmeldung konnte nicht gestartet werden.");
      setOauthPending(false);
    }
  }

  async function handleSkip() {
    await saveMailConnection({ onboarding_completed: true });
    await loadUser();
    navigate("/", { replace: true });
  }

  return {
    step,
    setStep,
    provider,
    setProvider,
    preset,
    setPreset,
    email,
    setEmail,
    imapUsername,
    setImapUsername,
    imapPassword,
    setImapPassword,
    imapHost,
    setImapHost,
    imapPort,
    setImapPort,
    outlookMailbox,
    setOutlookMailbox,
    outlookAuthMode,
    setOutlookAuthMode,
    testMessage,
    error,
    oauthPending,
    data,
    isLoading,
    saveMut,
    testMut,
    finishMut,
    handleSaveConfig,
    handleOutlookConnect,
    handleSkip,
  };
}
