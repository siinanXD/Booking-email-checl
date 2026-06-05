import { useQuery } from "@tanstack/react-query";
import { fetchWhatsAppPreview } from "@/lib/api/review";
import { Card } from "@/shared/ui/Card";

type Props = {
  correlationId: string | null;
};

export function ReviewWhatsAppCard({ correlationId }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ["whatsapp-preview", correlationId],
    queryFn: () => fetchWhatsAppPreview(correlationId!),
    enabled: Boolean(correlationId),
  });

  if (!correlationId) return null;

  return (
    <Card className="space-y-2">
      <h4 className="text-sm font-medium text-slate-800">WhatsApp-Vorschau</h4>
      {isLoading && <p className="text-xs text-slate-500">Lade…</p>}
      {data?.note && (
        <p className="text-xs text-amber-700">{data.note}</p>
      )}
      {(data?.messages ?? []).map((msg) => (
        <div
          key={`${msg.recipient_e164}-${msg.template_name}`}
          className="rounded border border-slate-200 p-2 text-xs"
        >
          <p className="font-medium">{msg.recipient_e164}</p>
          <p className="text-slate-500">{msg.template_name}</p>
          <ul className="mt-1 list-inside list-disc text-slate-600">
            {msg.template_params.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        </div>
      ))}
    </Card>
  );
}
