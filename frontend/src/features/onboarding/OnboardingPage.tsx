import { Link, Navigate, useSearchParams } from "react-router-dom";
import { Check, Zap } from "lucide-react";
import { useAuthStore } from "@/features/auth/authStore";
import { useAuthHydrated } from "@/features/auth/useAuthHydrated";
import { ConfigStep } from "./ConfigStep";
import { ProviderStep } from "./ProviderStep";
import { TestStep } from "./TestStep";
import { isAccountAdmin } from "./types";
import { useOnboardingForm } from "./useOnboardingForm";

const STEPS = [
  { key: "provider", label: "Anbieter" },
  { key: "config", label: "Konfiguration" },
  { key: "test", label: "Test" },
];

export function OnboardingPage() {
  const hydrated = useAuthHydrated();
  const [searchParams] = useSearchParams();
  const isEditMode = searchParams.has("edit");
  const user = useAuthStore((s) => s.user);
  const form = useOnboardingForm(hydrated && isAccountAdmin(user?.role));

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-400 border-t-transparent" />
          <p className="text-sm text-slate-500">Lade…</p>
        </div>
      </div>
    );
  }

  if (!isAccountAdmin(user?.role)) {
    return <Navigate to="/" replace />;
  }

  if (user?.role === "platform_admin") {
    return <Navigate to="/admin/overview" replace />;
  }

  if (user?.mail_onboarding_completed && !isEditMode) {
    return <Navigate to="/" replace />;
  }

  const currentStepIndex = STEPS.findIndex((s) => s.key === form.step);

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-950 p-4">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-40 top-1/4 h-80 w-80 rounded-full bg-indigo-600/10 blur-3xl" />
        <div className="absolute -right-40 bottom-1/4 h-80 w-80 rounded-full bg-violet-600/10 blur-3xl" />
      </div>

      <div className="relative w-full max-w-lg animate-fade-in">
        {/* Brand header */}
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-500/20 ring-1 ring-indigo-500/30">
            <Zap size={22} className="text-indigo-400" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Postfach verbinden
          </h1>
          <p className="mt-1.5 text-sm text-slate-400">
            Buchungsmails werden aus diesem Postfach gelesen.
          </p>
        </div>

        {/* Step indicator */}
        <div className="mb-6 flex items-center justify-center gap-0">
          {STEPS.map((step, idx) => {
            const done = idx < currentStepIndex;
            const active = idx === currentStepIndex;
            return (
              <div key={step.key} className="flex items-center">
                <div className="flex flex-col items-center gap-1.5">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-semibold transition-all ${
                      done
                        ? "border-emerald-500 bg-emerald-500 text-white"
                        : active
                          ? "border-indigo-500 bg-indigo-500 text-white"
                          : "border-slate-700 bg-slate-800 text-slate-500"
                    }`}
                  >
                    {done ? <Check size={14} /> : idx + 1}
                  </div>
                  <span
                    className={`text-[10px] font-medium ${
                      active ? "text-slate-200" : done ? "text-slate-400" : "text-slate-600"
                    }`}
                  >
                    {step.label}
                  </span>
                </div>
                {idx < STEPS.length - 1 && (
                  <div
                    className={`mx-3 mb-5 h-px w-12 transition-colors ${
                      done ? "bg-emerald-500/50" : "bg-slate-700"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Card */}
        <div className="rounded-2xl border border-white/[0.08] bg-white/[0.04] p-8 shadow-[0_8px_32px_rgba(0,0,0,0.4)] backdrop-blur-sm">
          {form.isLoading && (
            <div className="flex items-center gap-2 text-slate-400">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-600 border-t-indigo-400" />
              <span className="text-sm">Lade…</span>
            </div>
          )}

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
              oauthPending={form.oauthPending}
              data={form.data}
              onEmailChange={form.setEmail}
              onPresetChange={form.setPreset}
              onImapUsernameChange={form.setImapUsername}
              onImapPasswordChange={form.setImapPassword}
              onImapHostChange={form.setImapHost}
              onImapPortChange={form.setImapPort}
              onOutlookMailboxChange={form.setOutlookMailbox}
              onOutlookAuthModeChange={form.setOutlookAuthMode}
              onOutlookConnect={form.handleOutlookConnect}
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
              className="mt-4 w-full text-center text-xs text-slate-600 transition-colors hover:text-slate-400"
              onClick={form.handleSkip}
            >
              Überspringen
            </button>
          )}
        </div>

        <p className="mt-4 text-center text-xs text-slate-600">
          Einstellungen später unter{" "}
          <Link to="/settings" className="text-indigo-400 transition-colors hover:text-indigo-300">
            Einstellungen
          </Link>{" "}
          ändern.
        </p>
      </div>
    </div>
  );
}
