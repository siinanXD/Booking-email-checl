/**
 * Klartext-Hinweise für bekannte Meta/WhatsApp-Cloud-API-Fehlercodes.
 * Spiegelt _META_ERROR_HINTS im Backend (whatsapp_client.py) wider.
 */

export interface WhatsAppErrorHint {
  code: number;
  title: string;
  message: string;
  /** Optionaler Link zur Meta-Dokumentation/Aktion. */
  actionLabel?: string;
  actionUrl?: string;
}

const HINTS: Record<number, Omit<WhatsAppErrorHint, "code">> = {
  131030: {
    title: "Empfängernummer nicht freigegeben (Testmodus)",
    message:
      "Dein WhatsApp-Business-Konto ist noch im Testmodus und darf nur an bis zu " +
      "5 manuell freigegebene Nummern senden. Füge die Zielnummer im Meta-Dashboard " +
      "unter WhatsApp → API Setup → Recipient hinzu (per SMS-Code bestätigen) oder " +
      "schalte das Business-Konto live, um an beliebige Nummern zu senden.",
    actionLabel: "Meta-Dashboard öffnen",
    actionUrl: "https://developers.facebook.com/apps/",
  },
  131026: {
    title: "Nachricht nicht zustellbar",
    message:
      "Der Empfänger nutzt möglicherweise kein WhatsApp oder die Nummer hat das " +
      "falsche Format. Prüfe die Rufnummer im E.164-Format (z. B. +491701234567).",
  },
  190: {
    title: "Zugangstoken abgelaufen oder ungültig",
    message:
      "Erzeuge im Meta-Dashboard einen neuen Zugangstoken und trage ihn in den " +
      "WhatsApp-Einstellungen ein.",
    actionLabel: "Meta-Dashboard öffnen",
    actionUrl: "https://developers.facebook.com/apps/",
  },
  133010: {
    title: "Telefonnummer nicht registriert",
    message:
      "Die Telefonnummer ist nicht für die Cloud API registriert. Registriere sie " +
      "im Meta-Dashboard unter WhatsApp → API Setup.",
    actionLabel: "Meta-Dashboard öffnen",
    actionUrl: "https://developers.facebook.com/apps/",
  },
};

/**
 * Extrahiert einen bekannten Meta-Fehlercode aus einer Fehlermeldung und liefert
 * den passenden Hinweis (oder null, wenn unbekannt).
 */
export function parseWhatsAppErrorHint(
  errorText: string | null | undefined
): WhatsAppErrorHint | null {
  if (!errorText) return null;
  const match = errorText.match(/code\s+(\d+)/i);
  if (!match) return null;
  const code = Number(match[1]);
  const hint = HINTS[code];
  return hint ? { code, ...hint } : null;
}
