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
  return (
    <div className="mt-6 space-y-4">
      <p className="text-sm text-slate-600">
        Konfiguration gespeichert. Teste jetzt die Verbindung.
      </p>
      <Button className="w-full" onClick={onTest} disabled={testPending}>
        {testPending ? "Teste…" : "Verbindung testen"}
      </Button>
      {testMessage && (
        <p
          className={`text-sm ${testMessage.startsWith("Fehler") ? "text-red-600" : "text-green-700"}`}
        >
          {testMessage}
        </p>
      )}
      <Button className="w-full" onClick={onFinish} disabled={finishPending}>
        Fertig – zum Dashboard
      </Button>
      <Button type="button" variant="ghost" className="w-full" onClick={onSkip}>
        Später einrichten
      </Button>
    </div>
  );
}
