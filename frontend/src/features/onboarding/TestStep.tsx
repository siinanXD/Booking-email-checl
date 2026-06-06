import { CheckCircle2, XCircle, Wifi } from "lucide-react";
import { Button } from "@/shared/ui/Button";

type Props = {
  testMessage: string | null;
  testPending: boolean;
  finishPending: boolean;
  onTest: () => void;
  onFinish: () => void;
  onSkip: () => void;
};

export function TestStep({
  testMessage,
  testPending,
  finishPending,
  onTest,
  onFinish,
  onSkip,
}: Props) {
  const isError = testMessage?.startsWith("Fehler");
  const isSuccess = testMessage && !isError;

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-semibold text-white">Verbindung testen</p>
        <p className="mt-0.5 text-xs text-slate-400">
          Konfiguration gespeichert. Teste jetzt die Verbindung zum Postfach.
        </p>
      </div>

      <Button
        className="w-full py-2.5"
        variant="outline"
        onClick={onTest}
        disabled={testPending}
      >
        {testPending ? (
          <span className="flex items-center gap-2">
            <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-indigo-300/30 border-t-indigo-400" />
            Verbinde…
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <Wifi size={15} />
            Verbindung testen
          </span>
        )}
      </Button>

      {testMessage && (
        <div
          className={`flex items-start gap-2.5 rounded-lg border p-3 ${
            isError
              ? "border-red-500/20 bg-red-500/10"
              : "border-emerald-500/20 bg-emerald-500/10"
          }`}
        >
          {isError ? (
            <XCircle size={15} className="mt-0.5 flex-shrink-0 text-red-400" />
          ) : (
            <CheckCircle2 size={15} className="mt-0.5 flex-shrink-0 text-emerald-400" />
          )}
          <p className={`text-xs ${isError ? "text-red-300" : "text-emerald-300"}`}>
            {testMessage}
          </p>
        </div>
      )}

      {isSuccess && (
        <Button className="w-full py-2.5" onClick={onFinish} disabled={finishPending}>
          {finishPending ? (
            <span className="flex items-center gap-2">
              <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
              Wird gestartet…
            </span>
          ) : (
            "Fertig – zum Dashboard"
          )}
        </Button>
      )}

      {!isSuccess && (
        <Button className="w-full py-2.5" onClick={onFinish} disabled={finishPending} variant="secondary">
          Fertig – zum Dashboard
        </Button>
      )}

      <button
        type="button"
        className="w-full text-center text-xs text-slate-600 transition-colors hover:text-slate-400"
        onClick={onSkip}
      >
        Später einrichten
      </button>
    </div>
  );
}
