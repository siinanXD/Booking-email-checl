import { Link, Navigate, useSearchParams } from "react-router-dom";
import { Card } from "@/shared/ui/Card";
import { useAuthStore } from "@/features/auth/authStore";
import { ConfigStep } from "./ConfigStep";
import { ProviderStep } from "./ProviderStep";
import { TestStep } from "./TestStep";
import { isAccountAdmin } from "./types";
import { useOnboardingForm } from "./useOnboardingForm";

export function OnboardingPage() {
  const [searchParams] = useSearchParams();
  const isEditMode = searchParams.has("edit");
  const user = useAuthStore((s) => s.user);
  const form = useOnboardingForm(isAccountAdmin(user?.role));

  if (!isAccountAdmin(user?.role)) {
    return <Navigate to="/" replace />;
  }

  if (user?.mail_onboarding_completed && !isEditMode) {
    return <Navigate to="/" replace />;
  }

  const stepNum =
    form.step === "provider" ? 1 : form.step === "config" ? 2 : 3;

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4">
      <Card className="w-full max-w-lg">
        <h1 className="text-xl font-semibold text-slate-900">Postfach verbinden</h1>
        <p className="mt-1 text-sm text-slate-500">
          Schritt {stepNum} von 3 — Buchungsmails werden aus diesem Postfach gelesen.
        </p>

        {form.isLoading && <p className="mt-4 text-sm text-slate-500">Lade…</p>}

        {form.step === "provider" && (
          <ProviderStep
            provider={form.provider}
            onProviderChange={form.setProvider}
            onContinue={() => form.setStep("config")}
          />
        )}

        {form.step === "config" && (
          <ConfigStep
            provider={form.provider}
            email={form.email}
            preset={form.preset}
            imapUsername={form.imapUsername}
            imapPassword={form.imapPassword}
            imapHost={form.imapHost}
            imapPort={form.imapPort}
            outlookMailbox={form.outlookMailbox}
            outlookAuthMode={form.outlookAuthMode}
            error={form.error}
            savePending={form.saveMut.isPending}
            data={form.data}
            onEmailChange={form.setEmail}
            onPresetChange={form.setPreset}
            onImapUsernameChange={form.setImapUsername}
            onImapPasswordChange={form.setImapPassword}
            onImapHostChange={form.setImapHost}
            onImapPortChange={form.setImapPort}
            onOutlookMailboxChange={form.setOutlookMailbox}
            onOutlookAuthModeChange={form.setOutlookAuthMode}
            onBack={() => form.setStep("provider")}
            onSubmit={form.handleSaveConfig}
          />
        )}

        {form.step === "test" && (
          <TestStep
            testMessage={form.testMessage}
            testPending={form.testMut.isPending}
            finishPending={form.finishMut.isPending}
            onTest={() => form.testMut.mutate()}
            onFinish={() => form.finishMut.mutate()}
            onSkip={form.handleSkip}
          />
        )}

        {form.step !== "test" && (
          <button
            type="button"
            className="mt-4 w-full text-center text-sm text-slate-500 hover:text-slate-700"
            onClick={form.handleSkip}
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
