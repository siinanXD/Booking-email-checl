import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { fetchPropertyRecipients } from "@/lib/api/properties";
import { Card } from "@/shared/ui/Card";

/** Verweist auf die zentrale Empfänger-Verwaltung unter /properties. */
export function SettingsWhatsAppRecipientsCard() {
  const { data } = useQuery({
    queryKey: ["property-recipients"],
    queryFn: fetchPropertyRecipients,
  });
  const count = data?.items.length ?? 0;

  return (
    <Card className="space-y-2">
      <h3 className="font-medium text-slate-800">WhatsApp pro Unterkunft</h3>
      <p className="text-sm text-slate-600">
        {count} Unterkunft(en) mit konfigurierten Empfängern. Verwalten Sie
        Putzfrau- und Mitarbeiter-Nummern auf der Unterkünfte-Seite.
      </p>
      <Link
        to="/properties"
        className="text-sm font-medium text-indigo-600 hover:underline"
      >
        Zu Unterkünfte →
      </Link>
    </Card>
  );
}
