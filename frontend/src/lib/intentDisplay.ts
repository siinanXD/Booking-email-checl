/** Anzeige-Labels für Booking-Intents. */

const INTENT_LABELS: Record<string, string> = {
  new_booking: "Neue Buchung",
  cancellation: "Storno",
  change: "Änderung",
  guest_inquiry: "Gastnachricht",
  complaint: "Beschwerde",
  payment_issue: "Zahlung",
};

export function intentLabel(intent: string | null | undefined): string {
  if (!intent) return "—";
  return INTENT_LABELS[intent] ?? intent.replace(/_/g, " ");
}

/** Badge-Farben pro Intent (Tailwind-Töne für `Badge`). */
export function intentTone(intent: string | null | undefined): string {
  switch (intent) {
    case "new_booking":
      return "booking";
    case "cancellation":
      return "cancellation";
    case "change":
      return "change";
    case "guest_inquiry":
      return "inquiry";
    case "complaint":
      return "complaint";
    case "payment_issue":
      return "payment";
    default:
      return "default";
  }
}

export const INTENT_FILTER_OPTIONS = [
  { value: "", label: "Alle Intents" },
  { value: "new_booking", label: "Neue Buchung" },
  { value: "cancellation", label: "Storno" },
  { value: "change", label: "Änderung" },
  { value: "guest_inquiry", label: "Gastnachricht" },
  { value: "complaint", label: "Beschwerde" },
];
