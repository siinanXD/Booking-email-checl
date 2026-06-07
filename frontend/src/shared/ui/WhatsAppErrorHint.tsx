import { parseWhatsAppErrorHint } from "@/lib/whatsappErrors";

interface WhatsAppErrorHintProps {
  /** Roher Fehlertext, z. B. "Fehler: Meta API (400, code 131030): ...". */
  errorText: string | null | undefined;
}

/**
 * Zeigt bei bekannten Meta-Fehlercodes eine hervorgehobene Handlungsanweisung.
 * Rendert nichts, wenn kein bekannter Code erkannt wird.
 */
export function WhatsAppErrorHint({ errorText }: WhatsAppErrorHintProps) {
  const hint = parseWhatsAppErrorHint(errorText);
  if (!hint) return null;

  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm">
      <p className="font-medium text-amber-900">
        Hinweis (Meta-Code {hint.code}): {hint.title}
      </p>
      <p className="mt-1 text-amber-800">{hint.message}</p>
      {hint.actionUrl && (
        <a
          href={hint.actionUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 inline-block font-medium text-amber-900 underline"
        >
          {hint.actionLabel ?? "Mehr erfahren"}
        </a>
      )}
    </div>
  );
}
