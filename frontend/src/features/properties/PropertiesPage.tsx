import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  fetchPropertyHistory,
  fetchPropertyRecipients,
  fetchPropertySuggestions,
  savePropertyRecipients,
} from "@/lib/api/properties";
import { Button } from "@/shared/ui/Button";
import { Card } from "@/shared/ui/Card";
import { Input } from "@/shared/ui/Input";
import type { PropertyRecipientItem } from "@/lib/types/api";

export function PropertiesPage() {
  const queryClient = useQueryClient();
  const { data: recipients, isLoading } = useQuery({
    queryKey: ["property-recipients"],
    queryFn: fetchPropertyRecipients,
  });
  const { data: suggestions } = useQuery({
    queryKey: ["property-suggestions"],
    queryFn: () => fetchPropertySuggestions(15),
  });
  const { data: history } = useQuery({
    queryKey: ["property-history"],
    queryFn: () => fetchPropertyHistory({ limit: 20 }),
  });

  const [propertyRows, setPropertyRows] = useState<PropertyRecipientItem[]>([]);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!recipients) return;
    setPropertyRows(
      recipients.items.length > 0
        ? recipients.items
        : [{ property_name: "", phones: [""] }]
    );
  }, [recipients]);

  const saveMut = useMutation({
    mutationFn: () =>
      savePropertyRecipients(
        propertyRows
          .filter((row) => row.property_name.trim())
          .map((row) => ({
            property_name: row.property_name.trim(),
            phones: row.phones.map((p) => p.trim()).filter(Boolean),
          }))
      ),
    onSuccess: () => {
      setSaveMessage("Unterkünfte gespeichert.");
      void queryClient.invalidateQueries({ queryKey: ["property-recipients"] });
    },
    onError: () => setSaveMessage("Speichern fehlgeschlagen."),
  });

  function updatePropertyRow(
    index: number,
    field: "property_name" | "phones",
    value: string
  ) {
    setPropertyRows((rows) =>
      rows.map((row, i) => {
        if (i !== index) return row;
        if (field === "property_name") return { ...row, property_name: value };
        return { ...row, phones: [value] };
      })
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Unterkünfte</h2>
        <p className="text-sm text-slate-500">
          WhatsApp-Empfänger pro Unterkunft und Vorschläge aus Buchungs-Mails.
        </p>
      </div>

      <Card className="space-y-4">
        <h3 className="font-medium">Empfänger</h3>
        {isLoading ? (
          <p className="text-slate-500">Lade…</p>
        ) : (
          propertyRows.map((row, index) => (
            <div key={index} className="grid gap-2 sm:grid-cols-2">
              <Input
                placeholder="Unterkunftsname"
                value={row.property_name}
                onChange={(e) =>
                  updatePropertyRow(index, "property_name", e.target.value)
                }
              />
              <Input
                placeholder="WhatsApp +49…"
                value={row.phones[0] ?? ""}
                onChange={(e) => updatePropertyRow(index, "phones", e.target.value)}
              />
            </div>
          ))
        )}
        <Button onClick={() => saveMut.mutate()} disabled={saveMut.isPending}>
          Speichern
        </Button>
        {saveMessage && <p className="text-sm text-slate-600">{saveMessage}</p>}
      </Card>

      <Card>
        <h3 className="mb-2 font-medium">KI-Vorschläge (neue Namen)</h3>
        {(suggestions?.items.length ?? 0) === 0 ? (
          <p className="text-sm text-slate-500">Keine Vorschläge.</p>
        ) : (
          <ul className="text-sm space-y-1">
            {suggestions!.items.map((s) => (
              <li key={s.property_name}>
                {s.property_name}{" "}
                <span className="text-slate-400">({s.mail_count} Mails)</span>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card>
        <h3 className="mb-2 font-medium">Historie (letzte Buchungs-Mails)</h3>
        <ul className="text-sm space-y-2 max-h-64 overflow-y-auto">
          {(history?.items ?? []).map((h) => (
            <li key={h.correlation_id} className="border-b pb-1">
              <span className="font-medium">{h.property_name ?? "—"}</span> —{" "}
              {h.subject}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
